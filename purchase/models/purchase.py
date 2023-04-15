from datetime import date, timedelta

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.db.models import F, Q, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from moneyed import Money

from contact.models import Customer
from dea.models import Journal, JournalTypes
from invoice.models import PaymentTerm
from product.attributes import get_product_attributes_data
from product.models import (Attribute, ProductVariant, Stock, StockLot,
                            StockTransaction)

from ..managers import PurchaseQueryset


# multicurrency balance with balance field for ecery currency or a balance field with array of currency?
class Invoice(models.Model):
    # Fields
    created = models.DateTimeField(default=timezone.now, db_index=True)
    updated = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="purchased",
    )
    rate = models.DecimalField(max_digits=10, decimal_places=3)
    is_gst = models.BooleanField(default=False)
    gross_wt = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)
    net_wt = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)
    total = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)
    discount = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)
    balance = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)

    class BType(models.TextChoices):
        CASH = (
            "INR",
            _("Cash"),
        )
        GOLD = (
            "USD",
            _("Gold"),
        )
        SILVER = "AUD", _("Silver")

    metal_choices = (("Gold", "Gold"), ("Silver", "Silver"))
    status_choices = (
        ("Paid", "Paid"),
        ("PartiallyPaid", "PartiallyPaid"),
        ("Unpaid", "Unpaid"),
    )
    status = models.CharField(max_length=15, choices=status_choices, default="Unpaid")
    balancetype = models.CharField(
        max_length=30, choices=BType.choices, default=BType.CASH
    )
    metaltype = models.CharField(max_length=30, choices=metal_choices, default="Gold")
    due_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    # Relationship Fields
    supplier = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="purchases"
    )
    term = models.ForeignKey(
        PaymentTerm,
        on_delete=models.SET_NULL,
        related_name="purchase_term",
        blank=True,
        null=True,
    )
    journals = GenericRelation(Journal, related_query_name="purchase_doc")
    stock_txns = GenericRelation(StockTransaction)
    objects = PurchaseQueryset.as_manager()

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
        return self.purchaseitems.all()

    def get_gross_wt(self):
        return self.purchaseitems.aggregate(t=Sum("weight"))["t"]

    def get_net_wt(self):
        return self.purchaseitems.aggregate(t=Sum("net_wt"))["t"]

    # @property
    # def outstanding_balance(self):
    #     return self.balance - self.total_allocated_amount

    @classmethod
    def with_outstanding_balance(cls):
        return cls.objects.annotate(
            total_allocated_amount=Sum("paymentallocation__allocated_amount")
        ).annotate(outstanding_balance=F("balance") - F("total_allocated_amount"))

    # overdue_invoices = Invoice.with_outstanding_balance().filter(outstanding_balance__gt=0, due_date__lt=date.today())

    def get_total_balance(self):
        return self.purchaseitems.aggregate(t=Sum("total"))["t"]

    def get_allocations(self):
        paid = self.paymentallocation_set.aggregate(t=Sum("allocated_amount"))
        return paid["t"]

    @property
    def overdue_days(self):
        return (timezone.now().date() - self.due_date).days

    def get_balance(self):
        if self.get_total_payments() != None:
            return self.balance - self.get_total_payments()
        return self.total

    def save(self, *args, **kwargs):
        self.due_date = self.created + timedelta(days=self.term.due_days)
        # if self.is_gst:
        #     self.total += self.get_gst()
        self.total = self.balance + self.get_gst()

        super(Invoice, self).save(*args, **kwargs)

    def get_gst(self):
        return (self.balance * 3) / 100 if self.is_gst else 0

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
            return ledgerjournal, accountjournal

        return self.create_journals()

    def get_transactions(self):
        try:
            self.supplier.account
        except self.supplier.account.DOESNOTEXIST:
            self.supplier.save()

        inv = "GST INV" if self.is_gst else "Non-GST INV"
        money = Money(self.balance, self.balancetype)
        tax = Money(self.get_gst(), "INR")
        lt = [
            {"ledgerno": "Sundry Creditors", "ledgerno_dr": inv, "amount": money},
            {
                "ledgerno": "Sundry Creditors",
                "ledgerno_dr": "Input Igst",
                "amount": tax,
            },
        ]
        at = [
            {
                "ledgerno": "Sundry Creditors",
                "xacttypecode": "Dr",
                "xacttypecode_ext": "CRPU",
                "account": self.supplier.account,
                "amount": money + tax if self.is_gst else money,
            }
        ]
        return lt, at

    @transaction.atomic()
    def create_transactions(self):
        ledger_journal, Account_journal = self.get_journals()
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
    # Fields
    quantity = models.IntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    touch = models.DecimalField(max_digits=10, decimal_places=3)
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=3, blank=True)
    is_return = models.BooleanField(default=False, verbose_name="Return")
    makingcharge = models.DecimalField(
        max_digits=10, decimal_places=3, blank=True, null=True
    )
    # Relationship Fields
    product = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="products"
    )
    invoice = models.ForeignKey(
        "purchase.Invoice", on_delete=models.CASCADE, related_name="purchaseitems"
    )
    journal = GenericRelation(Journal, related_query_name="purchaseitems")

    class Meta:
        ordering = ("-pk",)

    def __str__(self):
        return "%s" % self.pk

    def get_absolute_url(self):
        return reverse("purchase:purchase_invoiceitem_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("purchase:purchase_invoiceitem_update", args=(self.pk,))

    def get_nettwt(self):
        return (self.weight * self.touch) / 100

    def save(self, *args, **kwargs):
        self.net_wt = self.get_nettwt()
        rate = self.invoice.rate if self.invoice.rate > 0 else 0
        self.total = self.net_wt * rate + self.makingcharge
        return super(InvoiceItem, self).save(*args, **kwargs)

    def update(self, *args, **kwargs):
        self.unpost()
        self.net_wt = self.get_nettwt()
        rate = self.invoice.rate if self.invoice.rate > 0 else 0
        self.total = self.net_wt * rate + self.makingcharge
        return super(InvoiceItem, self).update(*args, **kwargs)

    def create_journal(self):
        stock_journal = Journal.objects.create(
            content_object=self,
            journal_type=JournalTypes.SJ,
            desc=f"for purchase-item {self.invoice.pk}",
        )
        return stock_journal

    def get_journal(self):
        stock_journal = self.journal.filter(journal_type=JournalTypes.SJ)
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
                purchase_rate=self.invoice.rate,
                purchase=self.invoice,
            )
            stock_lot.transact(
                weight=self.weight,
                quantity=self.quantity,
                journal=journal,
                movement_type="P",
            )

        else:
            lot = StockLot.objects.get(stock__variant=self.product)
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
                self.product.stock_lots.get(
                    # variant=self.product,
                    purchase=self.invoice,
                ).transact(
                    journal=journal,
                    weight=self.weight,
                    quantity=self.quantity,
                    movement_type="PR",
                )
            except StockLot.DoesNotExist:
                print("Oops!while Posting  there was no said stock.  Try again...")
            # self.product.stock_lots.get(
            #     # variant=self.product,
            #     purchase=self.invoice,
            # ).transact(
            #     journal=journal,
            #     weight=self.weight,
            #     quantity=self.quantity,
            #     movement_type="P",
            # )
        else:
            try:
                self.product.stock_lots.get(
                    # variant=self.product,
                    purchase=self.invoice,
                ).transact(
                    journal=journal,
                    weight=self.weight,
                    quantity=self.quantity,
                    movement_type="P",
                )
            # self.product.stock_lots.get(
            #     # variant=self.product,
            #     purchase=self.invoice,
            # ).transact(
            #     journal=journal,
            #     weight=self.weight,
            #     quantity=self.quantity,
            #     movement_type="PR",
            # )
            except StockLot.DoesNotExist:
                print("Oops!while Unposting there was no said stock.  Try again...")
