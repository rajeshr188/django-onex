from django.db import models
from .models import Journal

class LoanGivenJournalManager(models.Manager):
    def get_queryset(self,*args,**kwargs):
        return super().get_queryset(*args,**kwargs).filter(
            type = Journal.Types.LG)


class LoanTakenJournalManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            # txn_type__XactTypeCode_ext='LT'
            # desc = 'Loan Taken'
            type=Journal.Types.LT
            )


class LoanReleaseJournalmanager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            # txn_type__XactTypeCode_ext='LR'
            # desc = 'Loan Released'
            type=Journal.Types.LR
            )


class LoanRepayJournalmanager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            # txn_type__XactTypeCode_ext='LP'
            # desc = 'Loan Repaid'
            type=Journal.Types.LP
            )
