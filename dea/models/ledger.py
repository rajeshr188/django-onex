from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.urls import reverse
from djmoney.models.fields import MoneyField
from moneyed import Money
from mptt.models import MPTTModel, TreeForeignKey

from ..managers import LedgerManager
from ..utils.currency import Balance
from .moneyvalue import MoneyValueField


# ledger account type  for COA ,asset,liability,revenue,expense,gain,loss
class AccountType(models.Model):
    AccountType = models.CharField(max_length=50)
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.AccountType


# ledger is chart of accounts
# add ledgerno
class Ledger(MPTTModel):
    AccountType = models.ForeignKey(AccountType, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    parent = TreeForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    objects = LedgerManager()

    class MPTTMeta:
        order_insertion_by = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "parent"], name="unique ledgername-parent"
            )
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("dea_ledger_detail", kwargs={"pk": self.pk})

    def get_latest_stmt(self):
        try:
            return self.ledgerstatements.latest()
        except LedgerStatement.DoesNotExist:
            return None

    def get_closing_balance(self):
        ls = self.get_latest_stmt()
        if ls is None:
            return Balance()
        else:
            return Balance(ls.ClosingBalance)

    def set_opening_bal(self, amount):
        # ensure there aint no txns before setting op bal if present then audit and adjust
        return LedgerStatement.objects.create(self, amount)

    def adjust(self, xacttypcode, amount):
        pass

    def ctxns(self, since=None):
        if since is not None:
            return self.credit_txns.filter(created__gte=since)
        else:
            return self.credit_txns.all()

    def dtxns(self, since=None):
        if since is not None:
            return self.debit_txns.filter(created__gte=since)
        else:
            return self.debit_txns.all()

    def audit(self):
        # this statement will serve as opening balance for this acc
        return LedgerStatement.objects.create(
            ledgerno=self, ClosingBalance=self.current_balance().monies()
        )

    def current_balance_wrt_descendants(self):
        descendants = [
            i.current_balance() for i in self.get_descendants(include_self=False)
        ]
        bal = sum(descendants, self.current_balance())
        return bal

    def current_balance(self):
        # decendants = self.get_descendants(include_self = True)

        # bal = [Balance([Money(r["total"], r["amount_currency"])
        #                 for r in acc.debit_txns.values("amount_currency").annotate(total = Sum("amount"))])
        #         -
        #        Balance([Money(r["total"], r["amount_currency"])
        #                 for r in acc.credit_txns.values("amount_currency").annotate(total = Sum("amount"))])
        #         for acc in decendants
        #         ]
        ls = self.get_latest_stmt()
        if ls is None:
            cb = Balance()
            since = None
        else:
            cb = ls.get_cb()
            since = ls.created
        c_bal = (
            Balance(
                [
                    Money(r["total"], r["amount_currency"])
                    for r in self.ctxns(since)
                    .values("amount_currency")
                    .annotate(total=Sum("amount"))
                ]
            )
            if self.ctxns(since=since)
            else Balance()
        )
        d_bal = (
            Balance(
                [
                    Money(r["total"], r["amount_currency"])
                    for r in self.dtxns(since)
                    .values("amount_currency")
                    .annotate(total=Sum("amount"))
                ]
            )
            if self.dtxns(since=since)
            else Balance()
        )

        bal = cb + d_bal - c_bal
        return bal


class LedgerTransactionManager(models.Manager):
    def create_txn(self, journal_entry, ledgerno, ledgerno_dr, amount):
        dr = Ledger.objects.get(name=ledgerno_dr)
        cr = Ledger.objects.get(name=ledgerno)
        txn = self.create(
            journal_entry=journal_entry, ledgerno=cr, ledgerno_dr=dr, amount=amount
        )
        return txn


class LedgerTransaction(models.Model):
    journal_entry = models.ForeignKey(
        "JournalEntry", on_delete=models.CASCADE, related_name="ltxns"
    )
    ledgerno = models.ForeignKey(
        Ledger, on_delete=models.CASCADE, related_name="credit_txns"
    )
    created = models.DateTimeField(
        auto_now_add=True,
        # unique = True
    )
    ledgerno_dr = models.ForeignKey(
        Ledger, on_delete=models.CASCADE, related_name="debit_txns"
    )
    # amount = models.DecimalField(max_digits=13, decimal_places=3)
    amount = MoneyField(
        max_digits=13,
        decimal_places=3,
        default_currency="INR",
        validators=[MinValueValidator(limit_value=0.0)],
    )
    objects = LedgerTransactionManager()

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "ledgerno",
                ]
            ),
            models.Index(
                fields=[
                    "ledgerno_dr",
                ]
            ),
        ]

    def __str__(self):
        return self.ledgerno.name


class LedgerStatement(models.Model):
    ledgerno = models.ForeignKey(
        Ledger, on_delete=models.CASCADE, related_name="ledgerstatements"
    )
    created = models.DateTimeField(
        # unique = True,
        auto_now_add=True
    )
    ClosingBalance = ArrayField(MoneyValueField(null=True, blank=True))

    class Meta:
        get_latest_by = "created"
        ordering = ["-created"]

    def __str__(self):
        return f"{self.created.date()} - {self.ledgerno} - {self.ClosingBalance}"

    def get_cb(self):
        return Balance(self.ClosingBalance)


# postgresql read-only-view
class Ledgerbalance(models.Model):
    ledgerno = models.OneToOneField(
        Ledger, on_delete=models.DO_NOTHING, primary_key=True
    )
    name = models.CharField(max_length=20)
    AccountType = models.CharField(max_length=20)
    created = models.DateTimeField()
    ClosingBalance = ArrayField(MoneyValueField(null=True, blank=True))
    cr = ArrayField(MoneyValueField(null=True, blank=True))
    dr = ArrayField(MoneyValueField(null=True, blank=True))

    class Meta:
        managed = False
        # db_table = "ledger_balance"
        db_table = "ledger_balance_plain"
        ordering = ["AccountType", "ledgerno__name"]

    def get_currbal(self):
        return self.get_cb() + self.get_dr() - self.get_cr()

    def get_cb(self):
        return Balance(self.ClosingBalance)

    def get_running_balance(self):
        return sum(
            [
                i.ledgerbalance.get_currbal()
                for i in self.ledgerno.get_descendants(include_self=True)
            ],
            Balance(),
        )

    def get_dr(self):
        return Balance(self.dr)

    def get_cr(self):
        return Balance(self.cr)
