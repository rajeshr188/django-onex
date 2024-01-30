import datetime
import math
from decimal import Decimal
# from qrcode.image.pure import PyImagingImage
from io import BytesIO

import qrcode
import qrcode.image.svg
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.db.models import (BooleanField, Case, DecimalField,
                              ExpressionWrapper, F, Func, Q, Sum, Value, When)
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear
from django.urls import reverse
from django.utils import timezone
from moneyed import Money

from contact.models import Customer
from dea.models import Journal,JournalEntry#, JournalTypes
from product.models import Rate

from ..managers import (LoanManager, LoanQuerySet, ReleasedManager,
                        UnReleasedManager)


class Loan(Journal):
    # Fields
    lid = models.IntegerField(blank=True, null=True)
    loanid = models.CharField(max_length=255, unique=True, db_index=True)
    has_collateral = models.BooleanField(default=False)
    pic = models.ImageField(upload_to="loan_pics/", null=True, blank=True)

    class LoanType(models.TextChoices):
        TAKEN = "Taken", "Taken"
        GIVEN = "Given", "Given"

    loan_type = models.CharField(
        max_length=10,
        choices=LoanType.choices,
        default=LoanType.GIVEN,
        null=True,
        blank=True,
    )

    itemdesc = models.TextField(
        max_length=100,
        verbose_name="Item",
        blank=True,
        null=True,
    )
    loanamount = models.PositiveIntegerField(
        verbose_name="Amount", default=0, null=True, blank=True
    )

    interest = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, null=True, blank=True
    )
    series = models.ForeignKey(
        "girvi.Series",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    # notifications = models.ManyToManyField(Notification)
    # Managers
    # objects = LoanManager.from_queryset(LoanQuerySet)()
    objects = LoanManager()
    released = ReleasedManager()
    unreleased = UnReleasedManager()
    lqs = LoanQuerySet.as_manager()

    class Meta:
        ordering = ("series", "lid")
        get_latest_by = "id"

    def __str__(self):
        return f"{self.loanid} - {self.loanamount} - {self.created_at.date()}"

    def get_absolute_url(self):
        return reverse("girvi:girvi_loan_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("girvi:girvi_loan_update", args=(self.pk,))

    @property
    def get_qr(self):
        factory = qrcode.image.svg.SvgImage
        img = qrcode.make(data=self.lid, image_factory=factory, box_size=20)
        stream = BytesIO()
        img.save(stream)
        svg = stream.getvalue().decode()
        return svg

    @property
    def is_released(self):
        return hasattr(self, "release")

    def get_loanamount(self):
        adjustments = self.adjustments.filter(as_interest=False).aggregate(
            total=Coalesce(Sum("amount_received"), 0)
        )["total"]
        items_total = (
            self.loanitems.aggregate(Sum("loanamount"))["loanamount__sum"] or 0
        )
        return items_total - adjustments

    def get_total_adjustments(self):
        as_int = 0
        as_amt = 0
        for a in self.adjustments.all():
            if a.as_interest:
                as_int += a.amount_received
            else:
                as_amt += a.amount_received
        data = {"int": as_int, "amt": as_amt}
        return data

    def noofmonths(self, date=datetime.datetime.now(timezone.utc)):
        cd = date  # datetime.datetime.now()
        nom = (cd.year - self.created_at.year) * 12 + cd.month - self.created_at.month
        return 1 if nom <= 0 else nom - 1

    def interestdue(self, date=datetime.datetime.now(timezone.utc)):
        return round(self.interest * self.noofmonths(date))

    def current_value(self):
        total_current_value = sum(
            loan_item.current_value() for loan_item in self.loanitems.all()
        )
        return total_current_value

    def total(self):
        return self.interestdue() + self.loanamount

    def due(self):
        a = self.get_total_adjustments()
        return self.loanamount + self.interestdue() - a["int"] - a["amt"]

    def is_worth(self):
        return self.current_value() < self.total()

    def get_worth(self):
        return self.current_value() - self.total()

    def calculate_months_to_exceed_value(self):
        if self.loanitems.exists():
            return math.ceil((self.total() - self.current_value()) / self.interest)
        return 0

    @property
    def get_pure(self):
        return self.loanitems.values("itemtype").annotate(
            pure_weight=Sum(
                ExpressionWrapper(
                    F("weight") * F("purity") * 0.01, output_field=DecimalField()
                )
            )
        )

    @property
    def get_weight(self):
        return self.loanitems.values("itemtype").annotate(total_weight=Sum("weight"))

    def get_next(self):
        return (
            Loan.objects.filter(series=self.series, lid__gt=self.lid)
            # .select_related("series","customer","release")
            .order_by("lid").first()
        )

    def get_previous(self):
        return (
            Loan.objects.filter(series=self.series, lid__lt=self.lid)
            # .select_related("series","customer","release")
            .order_by("lid").last()
        )

    def get_transactions(self):
        try:
            self.customer.account
        except:
            self.customer.save()
        amount = Money(self.loanamount, "INR")
        interest = Money(self.interest, "INR")
        if self.loan_type == self.LoanType.TAKEN:
            lt = [
                {"ledgerno": "Loans", "ledgerno_dr": "Cash", "amount": amount},
                {"ledgerno": "Cash", "ledgerno_dr": "Interest Paid", "amount": amount},
            ]
            at = [
                {
                    "ledgerno": "Loans",
                    "Xacttypecode": "Dr",
                    "xacttypecode_ext": "LT",
                    "account": self.customer.account,
                    "amount": amount,
                },
                {
                    "ledgerno": "Interest Payable",
                    "xacttypecode": "Cr",
                    "xacttypecode_ext": "IP",
                    "account": self.customer.account,
                    "amount": amount,
                },
            ]
        else:
            lt = [
                {
                    "ledgerno": "Cash",
                    "ledgerno_dr": "Loans & Advances",
                    "amount": amount,
                },
                {
                    "ledgerno": "Interest Received",
                    "ledgerno_dr": "Cash",
                    "amount": interest,
                },
            ]
            at = [
                {
                    "ledgerno": "Loans & Advances",
                    "xacttypecode": "Cr",
                    "xacttypecode_ext": "LG",
                    "account": self.customer.account,
                    "amount": amount,
                },
                {
                    "ledgerno": "Interest Received",
                    "xacttypecode": "Dr",
                    "xacttypecode_ext": "IR",
                    "account": self.customer.account,
                    "amount": interest,
                },
            ]
        return lt, at

    def save(self, *args, **kwargs):
        self.loanid = self.series.name + str(self.lid)
        super(Loan, self).save(*args, **kwargs)

    def get_items(self):
        return self.loanitems.all()

    @property
    def last_notified(self):
        notice = self.notification_set.last()
        return notice.created if notice else None

class LoanItem(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="loanitems")
    # item = models.ForeignKey(
    #                 "product.ProductVariant", on_delete=models.SET_NULL,
    #                 null=True,blank =True)
    pic = models.ImageField(upload_to="loan_pics/", null=True, blank=True)
    itype = (("Gold", "Gold"), ("Silver", "Silver"), ("Bronze", "Bronze"))
    itemtype = models.CharField(max_length=30, choices=itype, default="Gold")
    quantity = models.PositiveIntegerField(default=1)
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    purity = models.DecimalField(
        max_digits=10, decimal_places=2, default=75, blank=True, null=True
    )
    loanamount = models.DecimalField(max_digits=10, decimal_places=2)
    interestrate = models.DecimalField(max_digits=10, decimal_places=2)
    interest = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, blank=True, null=True
    )
    itemdesc = models.TextField(
        max_length=100, blank=True, null=True, verbose_name="Item"
    )

    def __str__(self):
        return f"{self.itemdesc} - {self.quantity}"

    def get_absolute_url(self):
        return reverse("girvi:girvi_loanitem_detail", args=(self.pk,))

    def get_hx_edit_url(self):
        kwargs = {"parent_id": self.loan.id, "id": self.id}
        return reverse("girvi:hx-loanitem-detail", kwargs=kwargs)

    def get_delete_url(self):
        return reverse(
            "girvi:girvi_loanitem_delete",
            kwargs={"id": self.id, "parent_id": self.loan.id},
        )

    def current_value(self):
        rate = (
            Rate.objects.filter(metal=self.itemtype).latest("timestamp").buying_rate
            if Rate.objects.filter(metal=self.itemtype).exists()
            else 0
        )
        return round(self.weight * self.purity * Decimal(0.01) * rate)

    def save(self, *args, **kwargs):
        self.interest = (self.interestrate / 100) * self.loanamount
        super().save(*args, **kwargs)
        # Update related Loan's total interest

# rename to payment when released create journals through payment
class Adjustment(Journal):
    
    amount_received = models.IntegerField(default=0)
    as_interest = models.BooleanField(default=True)

    adj_loan = models.ForeignKey(
        "girvi.Loan", on_delete=models.CASCADE, related_name="adjustments"
    )
    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.amount_received}=>loan{self.loan}"

    def get_absolute_url(self):
        return reverse("girvi:girvi_adjustment_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("girvi:girvi_adjustments_update", args=(self.pk,))

    def get_transactions(self):
        amount = Money(self.amount_received, "INR")
        interest = 0 if not self.as_interest else Money(self.amount_received, "INR")
        if self.loan_type == Loan.LoanTypes.TAKEN:
            # if self.customer.type == "Su":
            jrnl = Journal.objects.create(content_object=self, desc="Loan Adjustment")
            lt = [
                {"ledgerno": "Cash", "ledgerno_dr": "Loans", "amount": amount},
                {"ledgerno": "Cash", "ledgerno_dr": "Interest Paid", "amount": amount},
            ]
            at = [
                {
                    "ledgerno": "Loans",
                    "xacttypecode": "Cr",
                    "xacttypecode_ext": "LP",
                    "account": self.customer.account,
                    "amount": amount,
                },
                {
                    "ledgerno": "Interest Payable",
                    "xacttypecode": "Cr",
                    "xacttypecode_ext": "IP",
                    "account": self.customer.account,
                    "amount": amount,
                },
            ]
        else:
            jrnl = Journal.objects.create(content_object=self, desc="Loan Adjustment")
            lt = [
                {
                    "ledgerno": "Loans & Advances",
                    "ledgerno_dr": "Cash",
                    "amount": amount,
                },
                {
                    "ledgerno": "Interest Received",
                    "ledgerno_dr": "Cash",
                    "amount": amount,
                },
            ]
            at = [
                {
                    "ledgerno": "Loans & Advances",
                    "xacttypecode": "Dr",
                    "xacttypecode_ext": "LR",
                    "account": self.customer.account,
                    "amount": amount,
                },
                {
                    "ledgerno": "Interest Received",
                    "xacttypecode": "Dr",
                    "xacttypecode_ext": "IR",
                    "account": self.customer.account,
                    "amount": interest,
                },
            ]
        return lt, at

    def save(self, *args, **kwargs):
        super(Adjustment, self).save(*args, **kwargs)


class Statement(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, null=True, blank=True
    )
    # loan = models.ForeignKey(Loan, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.created}"

    def get_absolute_url(self):
        return reverse("girvi:girvi_loanstatement_detail", args=(self.pk,))

    @property
    def next(self):
        return Statement.objects.filter(id__gt=self.id).order_by("id").first()

    @property
    def previous(self):
        return Statement.objects.filter(id__lt=self.id).order_by("id").last()


class StatementItem(models.Model):
    statement = models.ForeignKey(Statement, on_delete=models.CASCADE)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.loan.loanid}"
