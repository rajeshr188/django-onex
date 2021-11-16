from django.contrib.contenttypes.models import ContentType
from django.db import models
from .ledger import LedgerTransaction
from .account import AccountTransaction
from django.contrib.contenttypes.fields import GenericForeignKey


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
    ST = "Stock", "Stock"
    AJ = "Approval", "Approval"
    AR = "Approval Return", "Approval Return"


class Journal(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=50, choices=JournalTypes.choices,
                            default=JournalTypes.BJ)
    desc = models.TextField(blank=True, null=True)
    # Below the mandatory fields for generic relation
    content_type = models.ForeignKey(ContentType,
                                     blank=True, null=True,
                                     on_delete=models.SET_NULL)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        get_latest_by = ('id')

    def __str__(self):
        return f"{self.id}:{self.desc}"

    def get_url_string(self):
        if self.content_type:
            return f"{self.content_type.app_label}_{self.content_type.model}_detail"

    def transact(self, lt, at):
        ltl = []
        atl = []
        for i in lt:
            ltl.append(LedgerTransaction(journal=self, ledgerno_id=i['ledgerno'],
                                         ledgerno_dr_id=i['ledgerno_dr'], amount=i['amount']))
        LedgerTransaction.objects.bulk_create(ltl, ignore_conflicts=True)

        for i in at:
            atl.append(AccountTransaction(journal=self, ledgerno_id=i['ledgerno'],
                                          XactTypeCode_id=i['xacttypecode'], XactTypeCode_ext_id=i['xacttypecode_ext'],
                                          Account_id=i['account'], amount=i['amount']))
        AccountTransaction.objects.bulk_create(atl, ignore_conflicts=True)

    def untransact(self, last_jrnl):
        if last_jrnl:
            ltxns = last_jrnl.ltxns.all()
            ltl = []
            for i in ltxns:
                ltl.append(LedgerTransaction(journal=self, ledgerno_id=i.ledgerno_dr_id,
                                             ledgerno_dr_id=i.ledgerno_id, amount=i.amount))
            LedgerTransaction.objects.bulk_create(ltl, ignore_conflicts=True)
            atxns = last_jrnl.atxns.all()
            for i in atxns:
                if i.XactTypeCode_id == 'Cr':  # 1
                    AccountTransaction.objects.create(journal=self, ledgerno_id=i.ledgerno_id, XactTypeCode_id='Dr',  # 2
                                                      XactTypeCode_ext_id='AC', Account_id=i.Account_id, amount=i.amount)  # 1
                else:
                    AccountTransaction.objects.create(journal=self, ledgerno_id=i.ledgerno_id, XactTypeCode_id='Cr',  # 1
                                                      XactTypeCode_ext_id='AD', Account_id=i.Account_id, amount=i.amount)  # 2
        else:
            print("No Last Journal to undo")
