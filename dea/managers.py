from django.db import models

class JournalTypes(models.TextChoices):
    BJ = "Base Journal", "base journal"
    LT = "Loan Taken", "Loan taken"
    LG = "Loan Given", "Loan given"
    LR = "Loan Released", "Loan released"
    LP = "Loan Paid", "Loan paid"
    IP = "Interest Paid", "Interest Paid"
    IR = "Interest Received", "Interest Received"
    SJ = "Sales", "Sales"
    SR = "Sales Return","Sales Return"
    RC = "Receipt", "Receipt"
    PJ = "Purchase", "Purchase"
    PR = "Purchase Return","Purchase Return"
    PY = "Payment", "Payment"

class LedgerManager(models.Manager):
    def close(self):
        pass
    # check all statements valid
    # delete all statements and transactions 
    # with last closing balance create a new statement that hence forth acts as op bal
    
class AccountManager(models.Manager):
    def close(self):
        pass
   # check all statements valid
#    or get closing bal from all txns and match with cb from txns since last cb
    # delete all statements and transactions
    # with last closing balance create a new statement that hence forth acts as op bal
class LoanGivenJournalManager(models.Manager):
    def get_queryset(self,*args,**kwargs):
        return super().get_queryset(*args,**kwargs).filter(
            type = JournalTypes.LG)

class LoanTakenJournalManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            # txn_type__XactTypeCode_ext='LT'
            # desc = 'Loan Taken'
            type=JournalTypes.LT
            )

class LoanReleaseJournalManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            # txn_type__XactTypeCode_ext='LR'
            # desc = 'Loan Released'
            type=JournalTypes.LR
            )

class LoanRepayJournalManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            # txn_type__XactTypeCode_ext='LP'
            # desc = 'Loan Repaid'
            type=JournalTypes.LP
            )
class InterestReceivedJournalManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            # txn_type__XactTypeCode_ext='LP'
            # desc = 'Loan Repaid'
            type=JournalTypes.IR
            )

class InterestPaidJournalManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            # txn_type__XactTypeCode_ext='LP'
            # desc = 'Loan Repaid'
            type=JournalTypes.IP
        )
        
class SalesJournalManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            type=JournalTypes.SJ
        )

class SalesReturnJournalManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            type=JournalTypes.SR
        )

class ReceiptJournalManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            type=JournalTypes.RC
        )

class PurchaseJournalManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            type=JournalTypes.PJ
        )

class PurchaseReturnJournalManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            type=JournalTypes.PR
        )

class PaymentJournalManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            type=JournalTypes.PY
        )

