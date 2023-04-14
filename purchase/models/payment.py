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


class Payment(models.Model):
    # Fields
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now_add=True, editable=False)
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

    payment_type = models.CharField(
        max_length=30,
        verbose_name="Currency",
        choices=BType.choices,
        default=BType.CASH,
    )
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    touch = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    rate = models.IntegerField(default=0)
    total = models.DecimalField(max_digits=10, decimal_places=3)
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
        Customer, on_delete=models.CASCADE, related_name="payments"
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
        total_allotted = (
            self.paymentallocation_set.aggregate(t=Sum("allocated_amount"))["t"]
            if self.paymentallocation_set.exists()
            else 0
        )
        print(f"total_allotted : {total_allotted}")

        if total_allotted == self.total:
            self.status = "Allotted"
        else:
            self.status = "Unallotted"
        self.save()

    def allot(self):
        if self.posted:
            print(f"allotting payment {self.id} type:{self.type} amount{self.total}")
            invpaid = 0 if self.amount_allotted() is None else self.amount_allotted()
            print(f" invpaid : {invpaid}")
            remaining_amount = self.total - invpaid
            print(f"remaining : {remaining_amount}")
            try:
                invtopay = (
                    Invoice.objects.filter(
                        supplier=self.supplier,
                        balancetype=self.type,
                        posted=True,
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
                    PaymentAllocation.objects.create(
                        payment=self, invoice=i, allocated_amount=bal
                    )
                    i.status = "Paid"
                else:
                    PaymentAllocation.objects.create(
                        payment=self, invoice=i, allocated_amount=remaining_amount
                    )
                    i.status = "PartiallyPaid"
                    remaining_amount = 0
                i.save()
            print("allotted payment")
            self.update_status()
        else:
            raise Exception("Payment not posted")

    def deallot(self):
        self.paymentallocation_set.all().delete()
        self.update_status()

    def amount_allotted(self):
        return (
            self.paymentallocation_set.aggregate(t=Sum("allocated_amount"))["t"]
            if self.paymentallocation_set.exists()
            else 0
        )

    def allocate(self):
        # get all unpaid invoices associated with this payment's customer
        unpaid_invoices = (
            Invoice.with_outstanding_balance()
            .filter(
                supplier=self.supplier,
                # paid=False,
                balancetype=self.type,
                posted=True,
                balance__gte=0,
                outstanding_balance__gt=0,
            )
            .exclude(status="Paid")
            .order_by("created")
        )

        # iterate over the unpaid invoices and allocate payment in order
        amount_remaining = self.total
        for invoice in unpaid_invoices:
            if amount_remaining <= 0:
                break

            # calculate the amount to allocate to this invoice
            amount_due = invoice.outstanding_balance
            print(f"amount_due:{amount_due}")
            print(f"amount_remaining:{amount_remaining}")
            amount_to_allocate = min(amount_due, amount_remaining)

            # create a PaymentAllocation object for this invoice and payment
            allocation = PaymentAllocation.objects.create(
                payment=self, invoice=invoice, allocated_amount=amount_to_allocate
            )

            # update the amount remaining to allocate
            amount_remaining -= amount_to_allocate

        # mark the payment as fully allocated if there is no amount remaining
        if amount_remaining <= 0:
            self.status = "Allotted"
            self.save()
        self.update_status()

    def create_journals(self):
        ledgerjournal = LedgerJournal.objects.create(
            journal_type=JournalTypes.LJ,
            content_object=self,
            desc="payment",
        )
        accountjournal = AccountJournal.objects.create(
            journal_type=JournalTypes.AJ,
            content_object=self,
            desc="payment",
        )
        return ledgerjournal, accountjournal

    def get_journals(self):
        ledgerjournal = self.journals.filter(journal_type=JournalTypes.LJ)
        accountjournal = self.journals.filter(journal_type=JournalTypes.AJ)

        if ledgerjournal.exists() and accountjournal.exists():
            return ledgerjournal, accountjournal

    def delete_journal(self):
        self.journals.all().delete()

    def get_transactions(self):
        jrnl = Journal.objects.create(
            journal_type=JournalTypes.PY,
            content_object=self,
            desc="payment",
        )

        money = Money(self.total, self.type)
        lt = [{"ledgerno": "Cash", "ledgerno_dr": "Sundry Creditors", "amount": money}]
        at = [
            {
                "ledgerno": "Sundry Creditors",
                "xacttypecode": "Dr",
                "xacttypecode_ext": "PYT",
                "account": self.supplier.account,
                "amount": money,
            }
        ]
        jrnl.transact(lt, at)
        self.posted = True
        self.save(update_fields=["posted"])
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
    allocated_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return "%s" % self.id

    def get_absolute_url(self):
        return reverse("purchase_paymentallocated_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("purchase_paymentallocated_update", args=(self.pk,))


"""
    This is a view that is used to get the outstanding balance of an invoice.
    SQL:
        CREATE VIEW invoice_payment_view AS 
        SELECT invoice.id, invoice.invoice_number, invoice.total_amount, 
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


class InvoicePaymentView(models.Model):
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
            amount_allocated=Sum("invoice_payments__allocated_amount")
        )

    class Meta:
        managed = False
        db_table = "invoice_payment_view"
