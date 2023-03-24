from django.db import models


class LedgerManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return (
            super()
            .get_queryset(*args, **kwargs)
            # .select_related('accounttype','ledgertransactions')
            .prefetch_related("ledgerstatements", "credit_txns", "debit_txns")
        )

    # check all statements valid
    # delete all statements and transactions
    # with last closing balance create a new statement that hence forth acts as op bal


class AccountManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return (
            super()
            .get_queryset(*args, **kwargs)
            .select_related("AccountType_Ext", "contact", "entity")
            .prefetch_related("accounttransactions", "accountstatements")
        )


# check all statements valid
#    or get closing bal from all txns and match with cb from txns since last cb
# delete all statements and transactions
# with last closing balance create a new statement that hence forth acts as op bal
