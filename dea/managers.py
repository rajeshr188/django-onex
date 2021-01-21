from django.db import models

class LoanGivenJournalManager(models.Manager):
    def get_queryset(self,*args,**kwargs):
        return super().get_queryset(*args,**kwargs).filter(
            desc = 'Loan Given')


class LoanTakenJournalManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            # txn_type__XactTypeCode_ext='LT'
            desc = 'Loan Taken'
            )


class LoanReleaseJournalmanager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            # txn_type__XactTypeCode_ext='LR'
            desc = 'Loan Released'
            )


class LoanRepayJournalmanager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            # txn_type__XactTypeCode_ext='LP'
            desc = 'Loan Repaid'
            )
