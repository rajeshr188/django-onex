from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction

from .account import AccountTransaction
from .ledger import LedgerTransaction


class JournalTypes(models.TextChoices):
    LJ = "LedgerJournal", "LedgerJournal"
    AJ = "AccountJournal", "AccountJournal"
    SJ = "StockJournal", "StockJournal"


class Journal(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    journal_type = models.CharField(
        max_length=50, choices=JournalTypes.choices, default=JournalTypes.LJ
    )
    desc = models.TextField(blank=True, null=True)
    # Below the mandatory fields for generic relation
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        get_latest_by = "id"
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.journal_type}{self.desc}"

    def get_url_string(self):
        # check if the object.content_type is a invoice item

        if self.content_type and self.content_object:
            from django.urls import reverse

            from purchase.models import Invoice as pinv
            from purchase.models import InvoiceItem as pi
            from sales.models import Invoice as sinv
            from sales.models import InvoiceItem as si

            si_ct = ContentType.objects.get_for_model(si)
            pi_ct = ContentType.objects.get_for_model(pi)
            sinv_ct = ContentType.objects.get_for_model(sinv)
            pinv_ct = ContentType.objects.get_for_model(pinv)

            if self.content_type in [si_ct, pi_ct]:
                # <!-- <a href="{% url ''|add:object.get_url_string pk=object.object_id %}"> -->
                # return f"{self.invoice.content_type.app_label}:{self.invoice.content_type.app_label}_{self.content_type.model}_detail"
                model = sinv_ct if self.content_type is si_ct else pinv_ct

                return reverse(
                    f"{self.content_type.app_label}:{self.content_type.app_label}_invoice_detail",
                    kwargs={"pk": self.content_object.invoice.pk},
                )

            # return f"{self.content_type.app_label}:{self.content_type.app_label}_{self.content_type.model}_detail"
            return reverse(
                f"{self.content_type.app_label}:{self.content_type.app_label}_{self.content_type.model}_detail",
                kwargs={"pk": self.object_id},
            )
        else:
            # print("returning none")
            return None

    @transaction.atomic()
    def transact(self, txns):
        # add transactions to the journal
        # check data integrity constraints before adding transactions
        if not self.check_data_integrity(txns):
            raise ValidationError("Data integrity violation.")

        if self.journal_type == "LedgerJournal":
            for i in txns:
                # print(f"cr: {i['ledgerno']}dr:{i['ledgerno_dr']}")
                LedgerTransaction.objects.create_txn(
                    self, i["ledgerno"], i["ledgerno_dr"], i["amount"]
                )
        elif self.journal_type == "AccountJournal":
            for i in txns:
                AccountTransaction.objects.create_txn(
                    self,
                    i["ledgerno"],
                    i["xacttypecode"],
                    i["xacttypecode_ext"],
                    i["account"],
                    i["amount"],
                )

    def check_data_integrity(self, transactions):
        # check data integrity constraints before adding transactions
        # for example, make sure the sum of debit amounts equals the sum of credit amounts
        # return True if all checks pass, False otherwise
        return True

    @transaction.atomic()
    def untransact(self, txns):
        if self.journal_type == "LedgerJournal":
            for i in txns:
                # print(f"txn:{i}")
                # print(f"cr: {i['ledgerno']} dr:{i['ledgerno_dr']}")
                LedgerTransaction.objects.create_txn(
                    self, i["ledgerno_dr"], i["ledgerno"], i["amount"]
                )
        elif self.journal_type == "AccountJournal":
            for i in txns:
                xacttypecode = ""
                xacttypecode_ext = ""
                if i["xacttypecode"] == "Cr":
                    xacttypecode = "Dr"
                    xacttypecode_ext = "AC"
                else:
                    xacttypecode = "Cr"
                    xacttypecode_ext = "AD"
                AccountTransaction.objects.create_txn(
                    self,
                    i["ledgerno"],
                    xacttypecode,
                    xacttypecode_ext,
                    i["account"],
                    i["amount"],
                )
