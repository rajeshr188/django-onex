from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction

from .account import AccountTransaction
from .ledger import LedgerTransaction


class JournalTypes(models.TextChoices):
    BJ = "Base Journal", "base journal"
    LT = "Loan Taken", "Loan taken"
    LG = "Loan Given", "Loan given"
    LR = "Loan Released", "Loan released"
    LP = "Loan Paid", "Loan paid"
    IP = "Interest Paid", "Interest Paid"
    IR = "Interest Received", "Interest Received"
    SJ = "Sales", "Sales"
    SR = "Sales Return", "Sales Return"
    RC = "Receipt", "Receipt"
    PJ = "Purchase", "Purchase"
    PR = "Purchase Return", "Purchase Return"
    PY = "Payment", "Payment"
    SI = "StockIN", "StockIN"
    SO = "StockOUT", "StockOUT"
    AP = "Approval", "Approval"
    AR = "Approval Return", "Approval Return"


class Journal(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    # this must go
    # contact = models.ForeignKey("contact.Customer", on_delete=models.CASCADE,
    # null=True,blank = True)
    journal_type = models.CharField(
        max_length=50, choices=JournalTypes.choices, default=JournalTypes.BJ
    )
    desc = models.TextField(blank=True, null=True)
    # Below the mandatory fields for generic relation
    content_type = models.ForeignKey(
        ContentType, blank=True, null=True, on_delete=models.SET_NULL
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        get_latest_by = "id"

    def __str__(self):
        return self.desc

    def get_url_string(self):
        if self.content_type and self.content_object:
            return f"{self.content_type.app_label}:{self.content_type.app_label}_{self.content_type.model}_detail"
        else:
            return None

    @transaction.atomic()
    def transact(self, lt=[], at=[]):
        for i in lt:
            print(f"cr: {i['ledgerno']}dr:{i['ledgerno_dr']}")
            LedgerTransaction.objects.create_txn(
                self, i["ledgerno"], i["ledgerno_dr"], i["amount"]
            )
        for i in at:
            AccountTransaction.objects.create_txn(
                self,
                i["ledgerno"],
                i["xacttypecode"],
                i["xacttypecode_ext"],
                i["account"],
                i["amount"],
            )

    @transaction.atomic()
    def untransact(self, last_jrnl):
        if last_jrnl:
            for i in last_jrnl.ltxns.all():
                LedgerTransaction.objects.create_txn(
                    self, i.ledgerno_dr, i.ledgerno, i.amount
                )
            for i in last_jrnl.atxns.all():
                xacttypecode = ""
                xacttypecode_ext = ""
                print(i.XactTypeCode.XactTypeCode)
                if i.XactTypeCode.XactTypeCode == "Cr":
                    xacttypecode = "Dr"
                    xacttypecode_ext = "AC"
                else:
                    xacttypecode = "Cr"
                    xacttypecode_ext = "AD"
                AccountTransaction.objects.create_txn(
                    self,
                    i.ledgerno,
                    xacttypecode,
                    xacttypecode_ext,
                    i.Account,
                    i.amount,
                )
        else:
            print("No Last Journal to undo")
