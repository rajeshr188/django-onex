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


class Receipt(models.Model):
    # Fields
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, null=True, blank=True
    )

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

    receipt_type = models.CharField(
        max_length=30,
        verbose_name="Currency",
        choices=BType.choices,
        default=BType.CASH,
    )
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    touch = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    rate = models.IntegerField(default=0)
    total = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    description = models.TextField(max_length=50, default="describe here")
    status_choices = (
        ("Allotted", "Allotted"),
        ("Partially Allotted", "PartiallyAllotted"),
        ("Unallotted", "Unallotted"),
    )
    status = models.CharField(
        max_length=18, choices=status_choices, default="Unallotted"
    )
    is_active = models.BooleanField(default=True)
    journals = GenericRelation(Journal, related_query_name="receipt_doc")
    # Relationship Fields
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="receipts",
        verbose_name="Customer"
    )
    invoices = models.ManyToManyField("sales.Invoice", through="ReceiptAllocation")

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return "%s" % self.id

    def get_absolute_url(self):
        return reverse("sales:sales_receipt_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("sales:sales_receipt_update", args=(self.pk,))

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=["is_active"])

    def get_line_totals(self):
        return self.receiptallocation_set.aggregate(t=Sum("allocated_amount"))["t"]

    def update_status(self):
        total_allotted = self.get_line_totals()
        if total_allotted is not None:
            if total_allotted == self.total:
                self.status = "Allotted"
            else:
                self.status = "Unallotted"
        self.save()

    def deallot(self):
        self.receiptline_set.all().delete()
        self.update_status()

    def allot(self):
        print(f"allotting receipt {self.id} amount: {self.total}")

        invpaid = 0 if self.get_line_totals() is None else self.get_line_totals()

        remaining_amount = self.total - invpaid

        try:
            invtopay = (
                Invoice.objects.filter(
                    customer=self.customer, balancetype=self.type, posted=True
                )
                .exclude(status="Paid")
                .order_by("created")
            )
            print(f"invtopay:{invtopay}")
        except IndexError:
            invtopay = None

        for i in invtopay:
            print(f"i:{i} bal:{i.get_balance()}")
            if remaining_amount <= 0:
                break
            bal = i.get_balance()
            if remaining_amount >= bal:
                remaining_amount -= bal
                ReceiptLine.objects.create(receipt=self, invoice=i, amount=bal)
                i.status = "Paid"
            else:
                ReceiptAllocation.objects.create(
                    receipt=self, invoice=i, allocated_amount=remaining_amount
                )
                i.status = "PartiallyPaid"
                remaining_amount = 0
            i.save()

        self.update_status()

    def create_journals(self):
        ledgerjournal = LedgerJournal.objects.create(
            content_object=self,
            desc="receipt",
            journal_type=JournalTypes.LJ,
        )
        accountjournal = AccountJournal.objects.create(
            content_object=self,
            desc="receipt",
            journal_type=JournalTypes.AJ,
        )
        return ledgerjournal, accountjournal

    def get_journals(self):
        ledgerjournal = self.journals.filter(journal_type=JournalTypes.LJ)
        accountjournal = self.journals.filter(journal_type=JournalTypes.AJ)

        if ledgerjournal.exists() and accountjournal.exists():
            return ledgerjournal, accountjournal
        return self.create_journals()

    def get_transactions(self):
        money = Money(self.total, self.type)
        lt = [{"ledgerno": "Sundry Debtors", "ledgerno_dr": "Cash", "amount": money}]
        at = [
            {
                "ledgerno": "Sundry Debtors",
                "xacttypecode": "Dr",
                "xacttypecode_ext": "RCT",
                "account": self.customer.account,
                "amount": money,
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


class ReceiptAllocation(models.Model):
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE)
    invoice = models.ForeignKey("sales.Invoice", on_delete=models.CASCADE)
    allocated_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return "%s" % self.id

    def get_absolute_url(self):
        return reverse("sales_receiptallocation_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("sales_receiptallocation_update", args=(self.pk,))


"""
    This is a view that is used to get the outstanding balance of an invoice.
    SQL:
        CREATE VIEW invoice_receipt_view AS 
        SELECT invoice.id, invoice.invoice_number, invoice.total_amount, 
            COALESCE(SUM(receipt_allocation.allocated_amount), 0) AS amount_allocated, 
            COALESCE(SUM(receipt.amount), 0) AS amount_paid 
        FROM invoice 
        LEFT JOIN receipt_allocation ON invoice.id = receipt_allocation.invoice_id 
        LEFT JOIN receipt ON receipt_allocation.receipt_id = receipt.id 
        GROUP BY invoice.id;

    invoice_receipts = InvoiceReceiptView.objects.all()
    for invoice in invoice_receipts:
        print(f"Invoice #{invoice.invoice_number}: Total amount: {invoice.total_amount}, Amount paid: {invoice.amount_paid}, Amount allocated: {invoice.amount_allocated}, Outstanding balance: {invoice.outstanding_balance}")

"""


class InvoiceReceiptView(models.Model):
    invoice_number = models.CharField(max_length=50)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_allocated = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def outstanding_balance(self):
        return self.total_amount - self.amount_paid

    @classmethod
    def get_queryset(cls):
        return cls.objects.annotate(
            amount_allocated=Sum("invoice_receipts__allocated_amount")
        )

    class Meta:
        managed = False
        db_table = "sales_receipt_view"
