from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.shortcuts import reverse
from django.utils import timezone
from moneyed import Money

from contact.models import Customer
from dea.models import JournalEntry#, JournalTypes


class ReleaseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("loan")


class Release(models.Model):
    # Fields
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, null=True, blank=True
    )
    releaseid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    interestpaid = models.IntegerField(default=0)

    # Relationship Fields
    loan = models.OneToOneField(
        "girvi.Loan", on_delete=models.CASCADE, related_name="release"
    )
    journal_entries = GenericRelation(JournalEntry, related_query_name="release_doc")
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

    def create_journal_entry(self):
        # ledgerjournal = Journal.objects.create(
        #     content_object=self, desc="Loan Released", journal_type=JournalTypes.LJ
        # )
        # accountjournal = Journal.objects.create(
        #     content_object=self, desc="Loan Released", journal_type=JournalTypes.AJ
        # )
        # return ledgerjournal, accountjournal
        return JournalEntry.objects.create(
            content_object=self, desc="Loan Released"
        )

    def delete_journal_entries(self):
        self.journal_entries.all().delete()

    def get_journal_entry(self):
        if not self.journal_entries.exists():
            return self.create_journal_entry()
        return self.journal_entries.first()
        # return self.journals.all()
        # ledgerjournal = self.journals.filter(
        #     release_doc=self, journal_type=JournalTypes.LJ
        # )
        # accountjournal = self.journals.filter(
        #     release_doc=self, journal_type=JournalTypes.AJ
        # )

        # if ledgerjournal.exists() and accountjournal.exists():
        #     return ledgerjournal, accountjournal
        # return self.create_journals()

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

    def create_transactions(self):
        journal_entry = self.get_journal_entry()
        lt,at = self.get_transactions()
        journal_entry.transact(lt,at)
        # ledgerjournal, accountjournal = self.get_journals()
        # lt, at = self.get_transactions()
        # ledgerjournal.transact(lt)
        # accountjournal.transact(at)

    def reverse_transactions(self):
        journal_entry = self.get_journal_entry()
        lt, at = self.get_transactions()
        journal_entry.untransact(lt,at)
        # ledgerJournal, accountJournal = self.get_journals()
        # ledgerJournal.untransact(lt)
        # accountJournal.untransact(at)
