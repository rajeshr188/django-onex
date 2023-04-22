from datetime import date, timedelta

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models import F, Q, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from moneyed import Money

from contact.models import Customer
from dea.models import Journal, JournalTypes
from dea.models.moneyvalue import MoneyValueField
from dea.utils.currency import Balance
from invoice.models import PaymentTerm
from product.attributes import get_product_attributes_data
from product.models import (Attribute, ProductVariant, Stock, StockLot,
                            StockTransaction)

from ..managers import PurchaseQueryset


# multicurrency balance with balance field for ecery currency
#  or a balance field with array of currency?
#  or a balance field with json of currency?
#  or a balance field with json of currency and balance
# or a seperate table for balance
class Invoice(models.Model):
    # Fields
    created = models.DateTimeField(default=timezone.now, db_index=True)
    updated = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        null=True,  # cant be null
        blank=True,  # cant be blank
        related_name="purchases_created",
    )
    # determine and implement how the changes in is_ratecut and is_gst affects item balance calculation
    # and which in turn affects vaoucher balance calculation
    is_ratecut = models.BooleanField(default=False)
    is_gst = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    status_choices = (
        ("Paid", "Paid"),
        ("PartiallyPaid", "PartiallyPaid"),
        ("Unpaid", "Unpaid"),
    )
    status = models.CharField(max_length=15, choices=status_choices, default="Unpaid")

    # Relationship Fields
    supplier = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="purchases",
        verbose_name=_("Supplier"),
    )
    term = models.ForeignKey(
        PaymentTerm,
        on_delete=models.SET_NULL,
        related_name="purchase_term",
        blank=True,
        null=True,
    )
    journals = GenericRelation(
        Journal,
        related_query_name="purchase_doc",
    )
    # objects = PurchaseQueryset.as_manager()

    class Meta:
        ordering = (
            "id",
            "created",
        )

    def __str__(self):
        return f"{self.id}"

    def get_absolute_url(self):
        return reverse("purchase:purchase_invoice_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("purchase:purchase_invoice_update", args=(self.pk,))

    def get_next(self):
        return Invoice.objects.filter(id__gt=self.id).order_by("id").first()

    def get_previous(self):
        return Invoice.objects.filter(id__lt=self.id).order_by("id").last()

    def get_invoiceitem_children(self):
        return self.purchase_items.all()

    def get_gross_wt(self):
        return self.purchase_items.aggregate(t=Sum("weight"))["t"]

    def get_net_wt(self):
        return self.purchase_items.aggregate(t=Sum("net_wt"))["t"]

    # @property
    # def outstanding_balance(self):
    #     return self.balance - self.total_allocated_amount

    @classmethod
    def with_outstanding_balance(cls):
        return cls.objects.annotate(
            total_allocated_amount=Sum("paymentallocation__allocated_amount")
        ).annotate(outstanding_balance=F("balance") - F("total_allocated_amount"))

    # overdue_invoices = Invoice.with_outstanding_balance().filter(outstanding_balance__gt=0, due_date__lt=date.today())

    # def get_total_balance(self):
    #     return self.purchaseitems.aggregate(t=Sum("total"))["t"]

    def get_allocations(self):
        paid = self.paymentallocation_set.aggregate(t=Sum("allocated_amount"))
        return paid["t"]

    @property
    def overdue_days(self):
        return (timezone.now().date() - self.due_date).days

    def get_balance(self):
        if self.get_total_payments() != None:
            # refactor since self.balance() return Balance() in multicurrency
            # self.get_total_payments() aslo return Balance() in multicurrency
            return self.balance() - self.get_total_payments()
        return self.balance()

    def save(self, *args, **kwargs):
        if not self.due_date:
            if self.term:
                self.due_date = self.created + timedelta(days=self.term.due_days)

        # self.cash_balance = self.cash_balance + self.get_gst()

        super(Invoice, self).save(*args, **kwargs)

    @property
    def balance(self):
        purchase_balance = self.purchase_balance
        try:
            # this should return Balance() multicurrency
            return Balance(purchase_balance.balances)
        except PurchaseBalance.DoesNotExist:
            return None

    def get_gst(self):
        return (self.cash_balance * 3) / 100 if self.is_gst else 0

    def create_journals(self):
        ledgerjournal = Journal.objects.create(
            content_object=self,
            journal_type=JournalTypes.LJ,
            desc="purchase",
        )
        accountjournal = Journal.objects.create(
            content_object=self,
            journal_type=JournalTypes.AJ,
            desc="purchase",
        )
        return ledgerjournal, accountjournal

    def get_journals(self):
        ledgerjournal = self.journals.filter(journal_type=JournalTypes.LJ)
        accountjournal = self.journals.filter(journal_type=JournalTypes.AJ)

        if ledgerjournal.exists() and accountjournal.exists():
            return ledgerjournal.first(), accountjournal.first()

        return self.create_journals()

    def get_transactions(self):
        try:
            self.supplier.account
        except self.supplier.account.DOESNOTEXIST:
            self.supplier.save()

        inv = "GST INV" if self.is_gst else "Non-GST INV"
        # money = Money(self.balance, self.balancetype)
        # tax = Money(self.get_gst(), "INR")
        # lt = [
        #     {"ledgerno": "Sundry Creditors", "ledgerno_dr": inv, "amount": money},
        #     {
        #         "ledgerno": "Sundry Creditors",
        #         "ledgerno_dr": "Input Igst",
        #         "amount": tax,
        #     },
        # ]
        # at = [
        #     {
        #         "ledgerno": "Sundry Creditors",
        #         "xacttypecode": "Dr",
        #         "xacttypecode_ext": "CRPU",
        #         "account": self.supplier.account,
        #         "amount": money + tax if self.is_gst else money,
        #     }
        # ]
        lt, at = [], []
        balance = self.balance
        cash_balance = balance.cash_balance or 0
        gold_balance = balance.gold_balance or 0
        silver_balance = balance.silver_balance or 0
        print("balance:")
        print(cash_balance, gold_balance, silver_balance)
        if self.is_ratecut:
            lt.append(
                {
                    "ledgerno": "Sundry Creditors",
                    "ledgerno_dr": inv,
                    "amount": cash_balance,
                }
            )
            at.append(
                {
                    "ledgerno": "Sundry Creditors",
                    "xacttypecode": "Dr",
                    "account": self.supplier.account,
                    "xacttypecode_ext": "CRPU",
                    "amount": cash_balance,
                }
            )
            if self.is_gst:
                lt.append(
                    {
                        "ledgerno": "Sundry Creditors",
                        "ledgerno_dr": "Input Igst",
                        "amount": tax,
                    }
                )
                at.append(
                    {
                        "ledgerno": "Sundry Creditors",
                        "xacttypecode": "Cr",
                        "xacttypecode_ext": "CRPU",
                        "account": self.supplier.account,
                        "amount": tax,
                    }
                )
        else:
            if gold_balance != 0:
                lt.append(
                    {
                        "ledgerno": "Sundry Creditors",
                        "ledgerno_dr": inv,
                        "amount": gold_balance,
                    }
                )
                at.append(
                    {
                        "ledgerno": "Sundry Creditors",
                        "xacttypecode": "Dr",
                        "xacttypecode_ext": "CRPU",
                        "account": self.supplier.account,
                        "amount": gold_balance,
                    }
                )

            # if self.silver_balance !=0:
            #     lt.append({"ledgerno": "Sundry Creditors", "ledgerno_dr": inv, "amount": silver_balance})
            #     at.append({"ledgerno": "Sundry Creditors", "xacttypecode": "Dr", "account": self.supplier.account, "amount": self.silver_balance})
        return lt, at

    @transaction.atomic()
    def create_transactions(self):
        ledger_journal, account_journal = self.get_journals()
        lt, at = self.get_transactions()

        ledger_journal.transact(lt)
        account_journal.transact(at)

    @transaction.atomic()
    def reverse_transactions(self):
        ledger_journal, Account_journal = self.get_journals()
        lt, at = self.get_transactions()

        ledger_journal.untransact(lt)
        account_journal.untransact(at)


class InvoiceItem(models.Model):
    # TODO:if saved and lot has sold items this shouldnt/cant be edited

    # Fields
    is_return = models.BooleanField(default=False, verbose_name="Return")
    quantity = models.IntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    touch = models.DecimalField(max_digits=10, decimal_places=3)
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0, blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    making_charge = models.DecimalField(
        max_digits=10, decimal_places=3, blank=True, null=True, default=0
    )
    hallmark_charge = models.DecimalField(
        max_digits=10, decimal_places=3, blank=True, null=True, default=0
    )

    metal_balance = MoneyField(max_digits=10, decimal_places=2, default_currency="USD")
    cash_balance = MoneyField(max_digits=10, decimal_places=2, default_currency="INR")
    # Relationship Fields
    product = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="products"
    )
    invoice = models.ForeignKey(
        "purchase.Invoice", on_delete=models.CASCADE, related_name="purchase_items"
    )
    journal = GenericRelation(
        Journal,
        # related_query_name="purchaseitems"
    )

    class Meta:
        ordering = ("-pk",)

    def __str__(self):
        return "%s" % self.pk

    def get_absolute_url(self):
        return reverse("purchase:purchase_purchaseitem_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("purchase:purchase_invoiceitem_update", args=(self.pk,))

    def get_hx_edit_url(self):
        kwargs = {"parent_id": self.invoice.id, "id": self.id}
        return reverse("purchase:purchase_invoiceitem_detail", kwargs=kwargs)

    def get_delete_url(self):
        return reverse(
            "purchase:purchase_invoiceitem_delete",
            kwargs={"id": self.id, "parent_id": self.invoice.id},
        )

    def get_nettwt(self):
        print(self.weight * (self.touch / 100))
        return self.weight * (self.touch / 100)

    def save(self, *args, **kwargs):
        self.net_wt = self.get_nettwt()
        self.rate = self.rate or 5000
        self.metal_balance_currency = (
            "USD" if "gold" in self.product.product.category.name else "EUR"
        )
        if self.invoice.is_ratecut:
            self.cash_balance = (
                self.net_wt * self.rate + self.making_charge + self.hallmark_charge
            )
            self.metal_balance = 0
        else:
            self.cash_balance = self.making_charge + self.hallmark_charge
            self.metal_balance = self.net_wt
            print(self.metal_balance)
        return super(InvoiceItem, self).save(*args, **kwargs)

    def balance(self):
        return Balance([self.metal_balance, self.cash_balance])

    def create_journal(self):
        stock_journal = Journal.objects.create(
            content_object=self,
            journal_type=JournalTypes.SJ,
            desc=f"for purchase-item {self.invoice.pk}",
        )
        return stock_journal

    def get_journal(self):
        stock_journal = self.journal
        if stock_journal.exists():
            return stock_journal.first()
        return self.create_journal()

    @transaction.atomic()
    def post(self, journal):
        """
        if not return item create/add a stocklot then transact,
        if return item then remove the lot from stocklot"""
        if not self.is_return:
            stock, created = Stock.objects.get_or_create(variant=self.product)
            stock_lot = StockLot.objects.create(
                variant=self.product,
                stock=stock,
                weight=self.weight,
                quantity=self.quantity,
                purchase_touch=self.touch,
                purchase_rate=self.rate,
                purchase_item=self,
            )
            stock_lot.transact(
                weight=self.weight,
                quantity=self.quantity,
                journal=journal,
                movement_type="P",
            )

        else:
            # each return item in purchase invoice item shall deduct same stock from any available lot
            lot = StockLot.objects.get(
                stock__variant=self.product, purchase=self.invoice
            )
            # lot = StockLotBalance.objects.get(Closing_wt__gte = self.weight,Closing_qty__gte = self.qty)
            lot.transact(
                journal=journal,
                weight=self.weight,
                quantity=self.quantity,
                movement_type="PR",
            )

    @transaction.atomic()
    def unpost(self, journal):
        """
        add lot back to stock lot if item is_return,
        remove lot from stocklot if item is not return item"""
        if self.is_return:
            try:
                lot = self.item_lots.latest("created")
                lot.transact(
                    journal=journal,
                    weight=lot.weight,
                    quantity=lot.quantity,
                    movement_type="P",
                )
            except StockLot.DoesNotExist:
                print("Oops!while Posting  there was no said stock.  Try again...")
        else:
            try:
                lot = self.item_lots.latest("created")
                lot.transact(
                    journal=journal,
                    weight=lot.weight,
                    quantity=lot.quantity,
                    movement_type="PR",
                )

            except StockLot.DoesNotExist:
                print("Oops!while Unposting there was no said stock.  Try again...")


"""
 initial logic for purchase balance
  SELECT purchase_invoice.id AS voucher_id,
    sum(pi.cash_balance) AS cash_balance,
    sum(pi.metal_balance) AS metal_balance
   FROM purchase_invoice
     JOIN purchase_invoiceitem pi ON pi.invoice_id = purchase_invoice.id
  GROUP BY purchase_invoice.id;
    --------------------------------------------
  improved logic:
  SELECT purchase_invoice.id AS voucher_id,
    sum(pi.cash_balance) AS cash_balance,
    sum(pi.metal_balance) FILTER(WHERE pi.metal_balance_currency = 'USD') AS gold_balance,
    sum(pi.metal_balance) FILTER(WHERE pi.metal_balance_currency = 'EUR') AS silver_balance
   FROM purchase_invoice
     JOIN purchase_invoiceitem pi ON pi.invoice_id = purchase_invoice.id
  GROUP BY 
    purchase_invoice.id;
  --------------------------------------------
  SELECT
    v.id,
    v.code,
    SUM(vi.balance_amount) FILTER (WHERE vi.balance_currency = 'USD') AS usd_balance,
    SUM(vi.balance_amount) FILTER (WHERE vi.balance_currency = 'EUR') AS eur_balance
FROM
    voucher_voucher AS v
    LEFT JOIN voucher_voucheritem AS vi ON v.id = vi.voucher_id
GROUP BY
    v.id,
    v.code;

  """


class PurchaseBalance(models.Model):
    voucher = models.OneToOneField(
        Invoice,
        on_delete=models.DO_NOTHING,
        primary_key=True,
        related_name="purchase_balance",
    )
    cash_balance = models.DecimalField(max_digits=10, decimal_places=2)
    gold_balance = models.DecimalField(max_digits=10, decimal_places=2)
    silver_balance = models.DecimalField(max_digits=10, decimal_places=2)
    balances = ArrayField(MoneyValueField(null=True, blank=True))

    class Meta:
        managed = False
        db_table = "purchase_balance"
