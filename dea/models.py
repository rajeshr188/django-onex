from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import connection, models, transaction
from django.db.models import Sum
from django.urls import reverse
from djmoney.models.fields import MoneyField
from moneyed import Money
from mptt.models import MPTTModel, TreeForeignKey
from psycopg2.extensions import AsIs, adapt, register_adapter
from psycopg2.extras import register_composite

from contact.models import Customer

from . import managers
from .utils.currency import Balance

MoneyValue = register_composite(
    "money_value", connection.cursor().cursor, globally=True
).type


def moneyvalue_adapter(value):
    return AsIs(
        "(%s,%s)::money_value" % (adapt(value.amount), adapt(value.currency.code))
    )


register_adapter(Money, moneyvalue_adapter)


class MoneyValueField(models.Field):
    description = "wrapper for money_value composite type in postgres"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return Money(value.amount, value.currency)

    def to_python(self, value):
        if isinstance(value, Money):
            return value
        if value is None:
            return value
        return Money(value.amount, value.currency.code)

    def get_prep_value(self, value):
        # in admin input box we enter 10 USD,20 INR,30 AUD

        if isinstance(value, Money):
            return value
        else:
            amount, currency = value.split()
            return Money(amount, currency)

    def db_type(self, connection):
        return "money_value"


# Create your models here.


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
    objects = managers.AccountManager()

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
            return self.accounttransactions.filter(created__gte=since)
        else:
            return self.accounttransactions.all()

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
        ls = self.latest_stmt()
        if ls is None:
            cb = Balance()
            ac_txn = self.txns()
        else:
            cb = ls.get_cb()
            ac_txn = self.txns(since=ls.created)

        credit = (
            ac_txn.filter(
                XactTypeCode_ext__in=["LT", "LR", "IR", "CPU", "CRPU", "RCT", "AC"]
            )
            .values("amount_currency")
            .annotate(total=Sum("amount"))
        )
        debit = (
            ac_txn.filter(XactTypeCode_ext__in=["LG", "LP", "IP", "PYT", "CRSL", "AD"])
            .values("amount_currency")
            .annotate(total=Sum("amount"))
        )
        credit_bal = Balance([Money(r["total"], r["amount_currency"]) for r in credit])

        debit_bal = Balance([Money(r["total"], r["amount_currency"]) for r in debit])
        bal = cb + (credit_bal - debit_bal)

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
    objects = managers.LedgerManager()

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


class Journal(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    type = models.CharField(
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
        if self.content_type:
            return f"{self.content_type.app_label}:{self.content_type.app_label}_{self.content_type.model}_detail"

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


class LedgerTransactionManager(models.Manager):
    def create_txn(self, journal, ledgerno, ledgerno_dr, amount):
        dr = Ledger.objects.get(name=ledgerno_dr)
        cr = Ledger.objects.get(name=ledgerno)
        print(f"cr:{cr}")
        print(f"dr {dr}")
        txn = self.create(journal=journal, ledgerno=cr, ledgerno_dr=dr, amount=amount)
        return txn


class LedgerTransaction(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name="ltxns")
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
    # ClosingBalance = models.DecimalField(max_digits=13, decimal_places=3)
    ClosingBalance = ArrayField(MoneyValueField(null=True, blank=True))

    class Meta:
        get_latest_by = "created"
        ordering = ["-created"]

    def __str__(self):
        return f"{self.created.date()} - {self.ledgerno} - {self.ClosingBalance}"

    def get_cb(self):
        return Balance(self.ClosingBalance)


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
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name="atxns")
    ledgerno = models.ForeignKey(Ledger, on_delete=models.CASCADE)
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

    def __str__(self):
        return f"{self.XactTypeCode_ext}"


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


# write a manager method for both acc and ledger that gets txns after self.statement.latest.created
