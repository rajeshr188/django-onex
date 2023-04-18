from datetime import date, timedelta

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.db.models import Func, Q, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from moneyed import Money
from sympy import content

from approval.models import ReturnItem
from contact.models import Customer
from dea.models import Journal, JournalTypes
from invoice.models import PaymentTerm
from product.models import StockLot, StockTransaction


class Month(Func):
    function = "EXTRACT"
    template = "%(function)s(MONTH from %(expressions)s)"
    output_field = models.IntegerField()


class Year(Func):
    function = "EXTRACT"
    template = "%(function)s(YEAR from %(expressions)s)"
    output_field = models.IntegerField()


class SalesQueryset(models.QuerySet):
    def gst(self):
        return self.filter(is_gst=True)

    def non_gst(self):
        return self.filter(is_gst=False)

    def total(self):
        return self.aggregate(
            cash=Sum("balance", filter=Q(balancetype="INR")),
            gold=Sum("balance", filter=Q(balancetype="USD")),
            silver=Sum("balance", filter=Q(balancetype="AUD")),
        )

    def total_with_ratecut(self):
        return self.aggregate(
            cash=Sum("balance", filter=Q(balancetype="INR")),
            cash_g=Sum("balance", filter=Q(balancetype="INR", metaltype="Gold")),
            cash_s=Sum("balance", filter=Q(balancetype="INR", metaltype="Silver")),
            cash_g_nwt=Sum("net_wt", filter=Q(balancetype="INR", metaltype="Gold")),
            cash_s_nwt=Sum("net_wt", filter=Q(balancetype="INR", metaltype="Silver")),
            gold=Sum("balance", filter=Q(balancetype="USD")),
            silver=Sum("balance", filter=Q(balancetype="AUD")),
        )

    def today(self):
        return self.filter(created__date=date.today())

    def cur_month(self):
        return self.filter(
            created__month=date.today().month, created__year=date.today().year
        )


class Invoice(models.Model):
    # Fields
    created = models.DateTimeField(default=timezone.now, db_index=True)
    updated = models.DateTimeField(auto_now_add=True, editable=False)
    created_by = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sold",
    )
    rate = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    is_gst = models.BooleanField(default=False)
    gross_wt = models.DecimalField(
        max_digits=14, decimal_places=4, default=0, null=True, blank=True
    )
    net_wt = models.DecimalField(
        max_digits=14, decimal_places=4, default=0, null=True, blank=True
    )
    total = models.DecimalField(
        max_digits=14, decimal_places=4, default=0.0, null=True, blank=True
    )
    discount = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    balance = models.DecimalField(max_digits=14, decimal_places=4, default=0)

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
        max_length=30,
        choices=BType.choices,
        default=BType.CASH,
        verbose_name="Bal_type",
    )
    metaltype = models.CharField(
        max_length=30, choices=metal_choices, default="Gold", verbose_name="Currency"
    )
    due_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    objects = SalesQueryset.as_manager()

    # Relationship Fields
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="sales",
        verbose_name="Customer"
    )
    term = models.ForeignKey(
        PaymentTerm,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sale_term",
    )
    # change to foreign
    approval = models.ForeignKey(
        "approval.Approval",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sales",
    )
    journals = GenericRelation(
        Journal,
        related_query_name="sales_doc",
    )

    class Meta:
        ordering = ("-created",)
        get_latest_by = "id"

    def __str__(self):
        return f"{self.id}"

    def get_absolute_url(self):
        return reverse("sales:sales_invoice_detail", kwargs={"pk": self.pk})

    def get_hx_url(self):
        return reverse("sales:hx-detail", kwargs={"id": self.id})

    def get_update_url(self):
        return reverse("sales:sales_invoice_update", args=(self.pk,))

    def get_delete_url(self):
        return reverse("sales:sales_invoice_delete", kwargs={"id": self.id})

    def get_invoiceitem_children(self):
        return self.saleitems.all()

    def get_next(self):
        return Invoice.objects.filter(id__gt=self.id).order_by("id").first()

    def get_previous(self):
        return Invoice.objects.filter(id__lt=self.id).order_by("id").last()

    def get_gross_wt(self):
        return self.saleitems.aggregate(t=Sum("weight"))["t"] or 0

    def get_net_wt(self):
        return self.saleitems.aggregate(t=Sum("net_wt"))["t"] or 0

    def get_total_balance(self):
        line_sum = self.saleitems.aggregate(t=Sum("total"))["t"] or 0
        if self.balancetype == self.BType.CASH and line_sum > 0:
            line_sum = self.rate * line_sum
        return line_sum

    def get_allocations(self):
        paid = self.receiptallocation_set.aggregate(t=Sum("allocated_amount"))
        return paid["t"]

    @property
    def overdue_days(self):
        return (timezone.now().date() - self.date_due).days

    def get_total_receipts(self):
        return (
            self.receiptallocation_set.aggregate(t=Sum("allocated_amount"))["t"] or None
        )

    def get_balance(self):
        if self.get_total_receipts() != None:
            return self.total - self.get_total_receipts()
        return self.total

    def save(self, *args, **kwargs):
        if self.id:
            self.gross_wt = self.get_gross_wt()
            self.net_wt = self.get_net_wt()
            self.balance = self.get_total_balance()

        self.due_date = self.created + timedelta(days=self.term.due_days)
        self.total = self.balance
        if self.is_gst:
            self.total += self.get_gst()

        return super(Invoice, self).save(*args, **kwargs)

    def update_bal(self):
        self.gross_wt = self.get_gross_wt()
        self.net_wt = self.get_net_wt()
        self.save()

    # def delete(self, *args, **kwargs):
    #     if self.approval:
    #         self.approval.is_billed = False
    #     super(Invoice, self).delete(*args, **kwargs)

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=["self.is_active"])

    def get_gst(self):
        if self.is_gst:
            return (self.balance * 3) / 100
        return 0

    def create_journals(self):
        ledgerjournal = Journal.objects.create(
            content_object=self,
            desc="sale",
            journal_type=JournalTypes.LJ,
        )
        accountjournal = Journal.objects.create(
            content_object=self,
            desc="sale",
            journal_type=JournalTypes.AJ,
        )
        return ledgerjournal, accountjournal

    def get_journals(self):
        ledgerjournal = self.journals.filter(journal_type=JournalTypes.LJ)
        accountjournal = self.journals.filter(journal_type=JournalTypes.AJ)

        if ledgerjournal.exists() and accountjournal.exists():
            return ledgerjournal.first(), accountjournal.first()
        return self.create_journals()

    def get_transactions(self):
        """
        if self.approval:

            before 16/4/2023 this logic was used to create sale items from approval items
            if any approval, return and bill

            for i in self.approval.items.filter(status="Pending"):
                apr = ReturnItem.objects.create(
                    line=i, quantity=i.quantity, weight=i.weight
                )
                apr.post()
                i.update_status()
            self.approval.is_billed = True
            self.approval.save()
            self.approval.update_status()
        """

        inv = "GST INV" if self.is_gst else "Non-GST INV"
        cogs = "GST COGS" if self.is_gst else "Non-GST COGS"
        money = Money(self.balance, self.balancetype)
        tax = Money(self.get_gst(), "INR")
        lt = [
            {"ledgerno": "Sales", "ledgerno_dr": "Sundry Debtors", "amount": money},
            {"ledgerno": inv, "ledgerno_dr": cogs, "amount": money},
            {
                "ledgerno": "Output Igst",
                "ledgerno_dr": "Sundry Debtors",
                "amount": tax,
            },
        ]
        at = [
            {
                "ledgerno": "Sales",
                "xacttypecode": "Cr",
                "xacttypecode_ext": "CRSL",
                "account": self.customer.account,
                "amount": money + tax,
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
    huid = models.CharField(max_length=6, null=True, blank=True, unique=True)
    quantity = models.IntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    # remove less stone
    less_stone = models.DecimalField(
        max_digits=10, decimal_places=3, default=0, verbose_name="less wt"
    )
    touch = models.DecimalField(max_digits=10, decimal_places=3)
    wastage = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=3)
    is_return = models.BooleanField(default=False, verbose_name="Return")
    makingcharge = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    # Relationship Fields
    product = models.ForeignKey(
        StockLot, on_delete=models.CASCADE, related_name="sold_items"
    )
    invoice = models.ForeignKey(
        "sales.Invoice", on_delete=models.CASCADE, related_name="saleitems"
    )
    approval_line = models.ForeignKey(
        "approval.ApprovalLine",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sold_items",
    )
    journal = GenericRelation(Journal, related_query_name="sale_items")

    class Meta:
        ordering = ("-pk",)

    def __str__(self):
        return "%s" % self.pk

    def get_absolute_url(self):
        return reverse("sales:sales_invoiceitem_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("sales:sales_invoiceitem_update", args=(self.pk,))

    def get_delete_url(self):
        return reverse(
            "sales:sales_invoiceitem_delete",
            kwargs={"id": self.id, "parent_id": self.invoice.id},
        )

    def get_hx_edit_url(self):
        kwargs = {"parent_id": self.invoice.id, "id": self.id}
        return reverse("sales:hx-invoiceitem-detail", kwargs=kwargs)

    def get_nettwt(self):
        if self.invoice.customer.type == "Re":
            return self.weight + self.wastage / 100
        else:
            return (self.weight * self.touch) / 100

    @property
    def get_total(self):
        if self.invoice.balancetype == "Cash":
            return self.get_nettwt() * self.invoice.rate
        else:
            return self.get_nettwt()

    def save(self, *args, **kwargs):
        super(InvoiceItem, self).save(*args, **kwargs)

    def create_journal(self):
        stock_journal = Journal.objects.create(
            content_object=self,
            journal_type=JournalTypes.SJ,
            desc=f"sale-item {self.invoice.pk}",
        )
        return stock_journal

    def get_journal(self):
        stock_journal = self.journal.filter(journal_type=JournalTypes.SJ)
        if stock_journal.exists():
            return stock_journal.first()
        return self.create_journal()

    @transaction.atomic()
    def post(self, jrnl):
        if not self.is_return:
            if self.approval_line:
                # unpost the approval line to return the stocklot from approvalline
                stock_journal = self.approval_line.get_journal()
                self.approval_line.unpost(stock_journal)
                self.approval_line.update_status()
            # post the invoice item to deduct the stock from stocklot
            self.product.transact(self.weight, self.quantity, jrnl, "S")
        else:
            self.product.transact(self.weight, self.quantity, jrnl, "SR")

    @transaction.atomic()
    def unpost(self, jrnl):
        if self.is_return:
            self.product.transact(self.weight, self.quantity, jrnl, "S")
        else:
            if self.approval_line:
                # post the approval line to deduct the stock from invoiceitem
                stock_journal = self.approval_line.get_journal()
                self.approval_line.post(stock_journal)
                self.approval_line.update_status()
            self.product.transact(self.weight, self.quantity, jrnl, "SR")
