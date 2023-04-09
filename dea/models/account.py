from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, F, Sum, Value, When, Window
from django.db.models.functions import Coalesce
from django.urls import reverse
from djmoney.models.fields import MoneyField
from moneyed import Money

from contact.models import Customer

from ..managers import AccountManager
from ..utils.currency import Balance
from .ledger import Ledger
from .moneyvalue import MoneyValueField


# cr credit,dr debit
class TransactionType_DE(models.Model):
    XactTypeCode = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


# sundry_debtor[dr],sundry_creditor[cr],let desc be unique
class AccountType_Ext(models.Model):
    XactTypeCode = models.ForeignKey(TransactionType_DE, on_delete=models.CASCADE)
    description = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.description


# person or organisation
class EntityType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# rameshbi[sundry debtor],ramlalji,narsa,mjk[sundry creditor]
# add accountno
class Account(models.Model):
    entity = models.ForeignKey(
        EntityType,
        null=True,
        on_delete=models.SET_NULL,
    )
    AccountType_Ext = models.ForeignKey(
        AccountType_Ext,
        on_delete=models.CASCADE,
    )

    contact = models.OneToOneField(
        Customer, on_delete=models.CASCADE, related_name="account"
    )
    objects = AccountManager()

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return f"{self.id}"

    def get_absolute_url(self):
        return reverse("dea_account_detail", kwargs={"pk": self.pk})

    def set_opening_bal(self, amount):
        # amount is a MoneyField
        # ensure there aint no txns before setting op bal if present then audit and adjust
        return AccountStatement.objects.create(self, ClosingBalance=Balance(amount))

    def adjust(self, amount, xacttypecode):
        pass

    def audit(self):
        ls = self.latest_stmt()
        if ls is None:
            since = None
        else:
            since = ls.created
        credit_t = self.total_credit(since=since).monies()
        debit_t = self.total_debit(since=since).monies()
        return AccountStatement.objects.create(
            AccountNo=self,
            ClosingBalance=self.current_balance().monies(),
            TotalCredit=credit_t,
            TotalDebit=debit_t,
        )

    def latest_stmt(self):
        try:
            return self.accountstatements.latest()
        except AccountStatement.DoesNotExist:
            return None

    def txns(self, since=None):
        if since:
            txns = self.accounttransactions.filter(created__gte=since).select_related(
                "journal",
                "journal__content_type",
                "Account",
                "XactTypeCode",
                "XactTypeCode_ext",
            )
        else:
            txns = self.accounttransactions.all().select_related(
                "journal",
                "journal__content_type",
                "Account",
                "XactTypeCode",
                "XactTypeCode_ext",
            )
        return txns

    def total_credit(self, since=None):
        txns = self.txns(since=since)
        return Balance(
            [
                Money(r["total"], r["amount_currency"])
                for r in txns.filter(XactTypeCode__XactTypeCode="Dr")
                .values("amount_currency")
                .annotate(total=Sum("amount"))
            ]
        )

    def total_debit(self, since=None):
        txns = self.txns(since=since)
        return Balance(
            [
                Money(r["total"], r["amount_currency"])
                for r in txns.filter(XactTypeCode__XactTypeCode="Cr")
                .values("amount_currency")
                .annotate(total=Sum("amount"))
            ]
        )

    def current_balance(self):
        return self.total_credit() - self.total_debit()
        # ls = self.latest_stmt()
        # if ls is None:
        #     cb = Balance()
        #     ac_txn = self.txns()
        # else:
        #     cb = ls.get_cb()
        #     ac_txn = self.txns(since=ls.created)

        # credit = (
        #     ac_txn.filter(
        #         XactTypeCode_ext__in=["LT", "LR", "IR", "CPU", "CRPU", "RCT", "AC"]
        #     )
        #     .values("amount_currency")
        #     .annotate(total=Sum("amount"))
        # )
        # debit = (
        #     ac_txn.filter(XactTypeCode_ext__in=["LG", "LP", "IP", "PYT", "CRSL", "AD"])
        #     .values("amount_currency")
        #     .annotate(total=Sum("amount"))
        # )
        # credit_bal = Balance([Money(r["total"], r["amount_currency"]) for r in credit])

        # debit_bal = Balance([Money(r["total"], r["amount_currency"]) for r in debit])
        # bal = cb + (credit_bal - debit_bal)
        # print(f"cb:{cb} credit_bal:{credit_bal} debit_bal:{debit_bal} bal:{bal}")
        return bal


# account statement for ext account
class AccountStatement(models.Model):
    AccountNo = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="accountstatements"
    )
    created = models.DateTimeField(
        # unique = True,
        auto_now_add=True
    )
    ClosingBalance = ArrayField(MoneyValueField(null=True, blank=True))
    TotalCredit = ArrayField(MoneyValueField(null=True, blank=True))
    TotalDebit = ArrayField(MoneyValueField(null=True, blank=True))

    class Meta:
        get_latest_by = "created"

    def __str__(self):
        return f"{self.id} | {self.AccountNo} = {self.ClosingBalance}({self.TotalDebit} - {self.TotalCredit})"

    def get_cb(self):
        return Balance(self.ClosingBalance)


# sales,purchase,receipt,payment,loan,release
class TransactionType_Ext(models.Model):
    XactTypeCode_ext = models.CharField(max_length=4, primary_key=True)
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.XactTypeCode_ext


class AccountTransactionManager(models.Manager):
    def create_txn(
        self, journal, ledgerno, xacttypecode, xacttypecode_ext, account, amount
    ):
        l = Ledger.objects.get(name=ledgerno)
        xc = TransactionType_DE.objects.get(XactTypeCode=xacttypecode)
        xc_ext = TransactionType_Ext.objects.get(XactTypeCode_ext=xacttypecode_ext)
        txn = self.create(
            journal=journal,
            ledgerno=l,
            XactTypeCode=xc,
            XactTypeCode_ext=xc_ext,
            Account=account,
            amount=amount,
        )
        return txn


class AccountTransaction(models.Model):
    journal = models.ForeignKey(
        "Journal", on_delete=models.CASCADE, related_name="atxns"
    )
    ledgerno = models.ForeignKey("Ledger", on_delete=models.CASCADE)
    created = models.DateTimeField(
        auto_now_add=True,
        # unique = True
    )
    XactTypeCode = models.ForeignKey(TransactionType_DE, on_delete=models.CASCADE)
    XactTypeCode_ext = models.ForeignKey(TransactionType_Ext, on_delete=models.CASCADE)
    Account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="accounttransactions"
    )
    amount = MoneyField(
        max_digits=13,
        decimal_places=3,
        default_currency="INR",
        validators=[MinValueValidator(limit_value=0.0)],
    )
    objects = AccountTransactionManager()

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "ledgerno",
                ]
            ),
        ]

    def __str__(self):
        return f"{self.XactTypeCode_ext}"


class Accountbalance(models.Model):
    entity = models.CharField(max_length=30)
    acc_type = models.CharField(max_length=30)
    acc_name = models.CharField(max_length=50)
    AccountNo = models.OneToOneField(
        Account, on_delete=models.DO_NOTHING, primary_key=True
    )
    created = models.DateTimeField()
    TotalCredit = ArrayField(MoneyValueField(null=True, blank=True))
    TotalDebit = ArrayField(MoneyValueField(null=True, blank=True))
    ClosingBalance = ArrayField(MoneyValueField(null=True, blank=True))
    cr = ArrayField(MoneyValueField(null=True, blank=True))
    dr = ArrayField(MoneyValueField(null=True, blank=True))

    class Meta:
        managed = False
        db_table = "account_balance"

    def get_currbal(self):
        return Balance(self.ClosingBalance) + Balance(self.dr) - Balance(self.cr)
