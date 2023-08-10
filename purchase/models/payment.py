from datetime import date, timedelta

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.db.models import F, Q, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from moneyed import Money

from contact.models import Customer
from dea.models import Journal, JournalTypes
from dea.utils.currency import Balance
from invoice.models import PaymentTerm
from product.attributes import get_product_attributes_data
from product.models import Attribute, ProductVariant, Stock, StockLot, StockTransaction
from purchase.models.purchase import Invoice


# how do you know which is gst payment?
class Payment(models.Model):
    # Fields
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now_add=True, editable=False)
    created_by = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, null=True, blank=True
    )
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    touch = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    rate = models.IntegerField(default=0)
    total = MoneyField(max_digits=10, decimal_places=3, default_currency="INR")
    description = models.TextField(max_length=100)
    status_choices = (
        ("Allotted", "Allotted"),
        ("Partially Allotted", "PartiallyAllotted"),
        ("Unallotted", "Unallotted"),
    )
    status = models.CharField(
        max_length=18, choices=status_choices, default="Unallotted"
    )
    journals = GenericRelation(Journal, related_query_name="payment_doc")
    # Relationship Fields
    supplier = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name=_("Supplier"),
    )
    invoices = models.ManyToManyField("purchase.Invoice", through="PaymentAllocation")

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return "%s" % self.id

    def get_absolute_url(self):
        return reverse("purchase:purchase_payment_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("purchase:purchase_payment_update", args=(self.pk,))

    def update_status(self):
        # total_allotted = self.get_line_totals()
        total_allotted = self.amount_allotted()
        if total_allotted == self.total:
            self.status = "Allotted"
        else:
            self.status = "Unallotted"
        self.save()

    def allot(self):
        print(
            f"allotting payment {self.id} type:{self.total_currency} amount{self.total}"
        )
        invpaid = 0 if self.amount_allotted() is None else self.amount_allotted()
        print(f" invpaid : {invpaid}")
        remaining_amount = self.total - invpaid
        print(f"remaining : {remaining_amount}")
        try:
            invtopay = (
                Invoice.objects.filter(
                    supplier=self.supplier,
                    balancetype=self.type,
                    balance__gte=0,
                )
                .exclude(status="Paid")
                .order_by("created")
            )
        except IndexError:
            invtopay = None
        print(f" invtopay :{invtopay}")

        for i in invtopay:
            print(f"i:{i} bal:{i.get_balance()}")
            if remaining_amount <= 0:
                break
            bal = i.get_balance()
            if remaining_amount >= bal:
                remaining_amount -= bal
                PaymentAllocation.objects.create(payment=self, invoice=i, allocated=bal)
                i.status = "Paid"
            else:
                PaymentAllocation.objects.create(
                    payment=self, invoice=i, allocated=remaining_amount
                )
                i.status = "PartiallyPaid"
                remaining_amount = 0
            i.save()
        print("allotted payment")
        self.update_status()

    def deallot(self):
        self.paymentallocation_set.all().delete()
        self.update_status()

    def amount_allotted(self):
        if self.paymentallocation_set.exists():
            amount_allotted = self.paymentallocation_set.aggregate(
                amount=Sum("allocated"),
            )
            return Money(amount_allotted["amount"], self.total_currency)
        else:
            return None

    def get_allocated_total(self):
        return (
            self.paymentallocation_set.aggregate(t=Sum("allocated"))["t"]
            if self.paymentallocation_set.exists()
            else None
        )

    def allocate(self):
        # get all unpaid invoices associated with this payment's customer and this payments currency type
        filters = {}
        filters["supplier"] = self.supplier
        print(f"total:{self.total_currency}")
        if self.total_currency == "INR":
            filters["outstanding_balance_cash__gt"] = 0
        elif self.total_currency == "USD":
            filters["outstanding_balance_gold__gt"] = 0
        elif self.total_currency == "AUD":
            filters["outstanding_balance_silver__gt"] = 0
        filter_q = Q(**filters)
        print(f"filter_q:{filter_q}")
        unpaid_invoices = (
            Invoice.with_outstanding_balance().filter(filter_q).order_by("created")
        )
        print(f"unpaid_invoices:{unpaid_invoices}")
        # iterate over the unpaid invoices and allocate payment in order
        amount_remaining = (
            self.total.amount
            if self.get_allocated_total() is None
            else self.total.amount - self.get_allocated_total()
        )
        for invoice in unpaid_invoices:
            if amount_remaining <= 0:
                break

            # calculate the amount to allocate to this invoice
            if self.total_currency == "INR":
                amount_due = invoice.outstanding_balance_cash
            elif self.total_currency == "USD":
                amount_due = invoice.outstanding_balance_gold
            elif self.total_currency == "AUD":
                amount_due = invoice.outstanding_balance_silver
            # amount_due = invoice.outstanding_balance
            print(f"amount_due:{amount_due}")
            print(f"amount_remaining:{amount_remaining}")
            amount_to_allocate = min(amount_due, amount_remaining)

            # create a PaymentAllocation object for this invoice and payment
            allocation = PaymentAllocation.objects.create(
                payment=self,
                invoice=invoice,
                allocated=Money(amount_to_allocate, self.total_currency),
            )

            # update the amount remaining to allocate
            amount_remaining -= amount_to_allocate

        # mark the payment as fully allocated if there is no amount remaining
        # if amount_remaining <= 0:
        #     self.status = "Allotted"
        #     self.save()
        self.update_status()

    def create_journals(self):
        ledgerjournal = Journal.objects.create(
            journal_type=JournalTypes.LJ,
            content_object=self,
            desc="payment",
        )
        accountjournal = Journal.objects.create(
            journal_type=JournalTypes.AJ,
            content_object=self,
            desc="payment",
        )
        return ledgerjournal, accountjournal

    def get_journals(self):
        ledgerjournal = self.journals.filter(journal_type=JournalTypes.LJ)
        accountjournal = self.journals.filter(journal_type=JournalTypes.AJ)

        if ledgerjournal.exists() and accountjournal.exists():
            return ledgerjournal.first(), accountjournal.first()

    def delete_journal(self):
        self.journals.all().delete()

    def get_transactions(self):
        lt = [
            {
                "ledgerno": "Cash",
                "ledgerno_dr": "Sundry Creditors",
                "amount": self.total,
            }
        ]
        at = [
            {
                "ledgerno": "Sundry Creditors",
                "xacttypecode": "Dr",
                "xacttypecode_ext": "PYT",
                "account": self.supplier.account,
                "amount": self.total,
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


class PaymentAllocation(models.Model):
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    invoice = models.ForeignKey("purchase.Invoice", on_delete=models.CASCADE)
    # allocated_amount = models.DecimalField(max_digits=10, decimal_places=2)
    allocated = MoneyField(
        max_digits=19,
        decimal_places=4,
        default_currency="INR",
        default=0,  # default value
    )

    def __str__(self):
        return f"{self.payment} - {self.invoice} - {self.allocated}"

    def get_absolute_url(self):
        return reverse("purchase_paymentallocated_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("purchase_paymentallocated_update", args=(self.pk,))


"""
    This is a view that is used to get the outstanding balance of an invoice.
    SQL:
        CREATE VIEW purchase_payment_view AS 
        SELECT invoice.id, invoice.total_amount, 
            COALESCE(SUM(payment_allocation.allocated_amount), 0) AS amount_allocated, 
            COALESCE(SUM(payment.amount), 0) AS amount_paid 
        FROM invoice 
        LEFT JOIN payment_allocation ON invoice.id = payment_allocation.invoice_id 
        LEFT JOIN payment ON payment_allocation.payment_id = payment.id 
        GROUP BY invoice.id;

    invoice_payments = InvoicePaymentView.objects.all()
    for invoice in invoice_payments:
        print(f"Invoice #{invoice.invoice_number}: Total amount: {invoice.total_amount}, Amount paid: {invoice.amount_paid}, Amount allocated: {invoice.amount_allocated}, Outstanding balance: {invoice.outstanding_balance}")

"""


class PurchasePaymentView(models.Model):
    purchase = models.CharField(max_length=50)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_allocated = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def outstanding_balance(self):
        return self.total_amount - self.amount_paid

    @classmethod
    def get_queryset(cls):
        return cls.objects.annotate(
            amount_allocated=Sum("invoice_payments__allocated_amount")
        )

    class Meta:
        managed = False
        db_table = "invoice_payment_view"
