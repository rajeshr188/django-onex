from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.contrib.postgres.fields.ranges import DateRangeField
from django.db import models
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce


# Create your models here.
class Account(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    def get_latest_statement(self):
        return self.statement_set.order_by("-created").first()

    def audit_trial(self):
        last_audit = self.get_latest_statement()
        bal = 0
        if last_audit:
            bal = self.get_balance() + last_audit.closing_balance
        else:
            bal = self.get_balance()

        return Statement.objects.create(account=self, closing_balance=bal)

    def audit(self):
        st = self.audit_trial()
        self.statement_set.exclude(id=st.id).delete()

    def get_balance(self, txn_type=None):
        bal = 0
        last_audit = self.get_latest_statement()
        txns = self.transaction_set
        if last_audit is not None:
            txns = txns.filter(
                date__gt=last_audit.created,
            )
        if txn_type is not None:
            txns = txns.filter(txn_type=txn_type).aggregate(t=models.Sum("amount"))
            bal = txns["t"]
        else:
            txns = txns.aggregate(
                cr=Coalesce(Sum("amount", filter=Q(txn_type="Cr")), 0),
                dr=Coalesce(Sum("amount", filter=Q(txn_type="Dr")), 0),
            )
            bal = txns["cr"] - txns["dr"]
        return bal

    def set_op_bal(self, amount):
        try:
            opbal = Statement.objects.create(account=self, closing_balance=amount)
            opbal.save()
        except:
            print("failed setting opening balance")


class Transaction(models.Model):
    date = models.DateField(db_index=True)
    account = models.ForeignKey("sea.Account", on_delete=models.CASCADE)
    txn_choices = (
        ("Cr", "Credit"),
        (
            "Dr",
            "Debit",
        ),
    )
    txn_type = models.CharField(choices=txn_choices, max_length=2)
    amount = models.DecimalField(max_digits=14, decimal_places=3)

    def __str__(self):
        return f"{self.date}:{self.account.name}:{self.txn_type}:{self.amount}"


class Book(models.Model):
    name = models.CharField(max_length=20)
    daterange = DateRangeField()
    book_type_choices = (
        ("Daily", "Daily"),
        ("Monthly", "Monthly"),
        ("Yearly", "Yearly"),
    )
    book_type = models.CharField(choices=book_type_choices, max_length=10)

    def __str__(self) -> str:
        return f"{self.daterange}"


class Statement(models.Model):
    created = models.DateField()
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    closing_balance = models.DecimalField(max_digits=14, decimal_places=3)

    def __str__(self):
        return f" {self.account.name} Bal: {self.closing_balance}"


class drs(models.Model):
    period = DateTimeRangeField()
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    cb = models.DecimalField(max_digits=14, decimal_places=3)

    def __str__(self):
        return f"{self.period} {self.account.name} {self.cb} "
