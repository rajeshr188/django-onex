from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.shortcuts import reverse
from django.utils import timezone
from moneyed import Money
from polymorphic.managers import PolymorphicManager

from contact.models import Customer
from dea.models import Journal, JournalEntry  # , JournalTypes


class ReleaseManager(PolymorphicManager):
    def get_queryset(self):
        return super().get_queryset().select_related("release_loan")


class Release(Journal):
    # Fields
    releaseid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    interestpaid = models.IntegerField(default=0)

    # Relationship Fields
    release_loan = models.OneToOneField(
        "girvi.Loan", on_delete=models.CASCADE, related_name="release"
    )
    # manager
    objects = ReleaseManager()

    class Meta:
        ordering = ("-id",)

    def __str__(self):
        return "%s" % self.releaseid

    def get_absolute_url(self):
        return reverse("girvi:girvi_release_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("girvi:girvi_release_update", args=(self.pk,))

    def total_received(self):
        return self.loan.loanamount + self.interestpaid

    def get_transactions(self):
        amount = Money(self.loan.loanamount, "INR")
        interest = Money(self.interestpaid, "INR")
        if not self.loan.customer.account:
            s = self.loan.customer
            s.customer.name += ""
            s.save()
        if self.loan.loan_type == self.loan.LoanType.TAKEN:
            # jrnl = Journal.objects.create(content_object=self, desc="Loan Repaid")
            lt = [
                {"ledgerno": "Cash", "ledgerno_dr": "Loans", "amount": amount},
                {"ledgerno": "Cash", "ledgerno_dr": "Interest Paid", "amount": amount},
            ]
            at = [
                {
                    "ledgerno": "Loans",
                    "xacttypecode": "Cr",
                    "xacttypecode_ext": "LR",
                    "account": self.loan.customer.account,
                    "amount": amount,
                },
                {
                    "ledgerno": "Interest Payable",
                    "xacttypecode": "Cr",
                    "xacttypecode_ext": "IP",
                    "account": self.loan.customer.account,
                    "amount": amount,
                },
            ]
        else:
            # jrnl = Journal.objects.create(content_object=self, desc="Loan Released")
            lt = [
                {
                    "ledgerno": "Loans & Advances",
                    "ledgerno_dr": "Cash",
                    "amount": amount,
                },
                {
                    "ledgerno": "Interest Received",
                    "ledgerno_dr": "Cash",
                    "amount": amount,
                },
            ]
            at = [
                {
                    "ledgerno": "Loans & Advances",
                    "xacttypecode": "Dr",
                    "xacttypecode_ext": "LR",
                    "account": self.loan.customer.account,
                    "amount": amount,
                },
                {
                    "ledgerno": "Interest Received",
                    "xacttypecode": "Dr",
                    "xacttypecode_ext": "IR",
                    "account": self.loan.customer.account,
                    "amount": interest,
                },
            ]
        return lt, at
