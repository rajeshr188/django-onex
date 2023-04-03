import datetime
from decimal import Decimal
# from qrcode.image.pure import PyImagingImage
from io import BytesIO

import qrcode
import qrcode.image.svg
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import DateRangeField
from django.db import models, transaction
from django.db.models import (BooleanField, Case, DecimalField,
                              ExpressionWrapper, F, Q, Sum, When)
from django.db.models.functions import ExtractMonth, ExtractYear
from django.urls import reverse
from django.utils import timezone
from moneyed import Money

from contact.models import Customer
from dea.models import Journal, JournalTypes
from product.models import Rate


class LoanQuerySet(models.QuerySet):
    def posted(self):
        return self.filter(posted=True)

    def unposted(self):
        return self.filter(posted=False)

    def released(self):
        return self.filter(release__isnull=False)

    def unreleased(self):
        return self.filter(release__isnull=True)

    def with_due(self):
        current_time = timezone.now()
        return self.annotate(
            months_since_created=ExpressionWrapper(
                (ExtractYear(current_time) - ExtractYear(F("created"))) * 12
                + (ExtractMonth(current_time) - ExtractMonth(F("created")))
                + (current_time.day - F("created__day")) / 30,
                output_field=models.FloatField(),
            ),
            total_interest=ExpressionWrapper(
                (F("loanamount") * F("interestrate") * F("months_since_created")) / 100,
                output_field=models.FloatField(),
            ),
            total_due=F("loanamount") + F("total_interest"),
        )

    def with_current_value(self):
        latest_rate = Rate.objects.latest("timestamp")
        return self.annotate(
            current_value=ExpressionWrapper(
                (F("itemweight") * 75) / 100 * latest_rate.buying_rate,
                output_field=models.FloatField(),
            )
        )

    def with_is_overdue(self):
        is_overdue = Case(
            When(total_due__gt=F("current_value"), then=True),
            default=False,
            output_field=BooleanField(),
        )
        return self.annotate(is_overdue=is_overdue)

    def with_total_loanamount(self):
        return self.aggregate(
            total=Sum("loanamount"),
            gold=Sum("loanamount", filter=Q(itemtype="Gold")),
            silver=Sum("loanamount", filter=Q(itemtype="Silver")),
            bronze=Sum("loanamount", filter=Q(itemtype="Bronze")),
        )

    def with_total_interest(self):
        today = datetime.date.today()

        return self.annotate(
            no_of_months=ExpressionWrapper(
                today.month
                - F("created__month")
                + 12 * (today.year - F("created__year")),
                output_field=DecimalField(decimal_places=2),
            ),
            loan_interest=F("interestrate") * F("loanamount") * F("no_of_months") / 100,
        ).aggregate(Sum("loan_interest"))["loan_interest__sum"]


class LoanManager(models.Manager):
    # def get_queryset(self):
    #     return super().get_queryset().select_related("series", "release", "customer")

    def get_queryset(self):
        return LoanQuerySet(self.model, using=self._db).select_related(
            "series", "release", "customer"
        )

    def released(self):
        return self.get_queryset().released()

    def unreleased(self):
        return self.get_queryset().unreleased()

    def with_total_interest(self):
        return self.get_queryset().with_total_interest()

    def with_total_loanamount(self):
        return self.get_queryset().with_total_loanamount()

    def posted(self):
        return self.get_queryset().posted()

    def unposted(self):
        return self.get_queryset().unposted()

    def with_due(self):
        return self.get_queryset().with_due()

    def with_current_value(self):
        return self.get_queryset().with_current_value()

    def with_is_overdue(self):
        return self.get_queryset().with_is_overdue()


class ReleasedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(release__isnull=False)


class UnReleasedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(release__isnull=True)


# sinked_loans = Loan.objects.with_due().with_current_value().with_is_overdue().filter(is_overdue = True)
# sinked_loans.filter(created__year_gt = 2021)
# bursting possibilities :-;
class Loan(models.Model):
    # Fields
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, null=True, blank=True
    )
    lid = models.IntegerField(blank=True, null=True)
    loanid = models.CharField(max_length=255, unique=True)
    itype = (("Gold", "Gold"), ("Silver", "Silver"), ("Bronze", "Bronze"))
    itemtype = models.CharField(max_length=30, choices=itype, default="Gold")
    itemdesc = models.TextField(max_length=100)
    itemweight = models.DecimalField(max_digits=10, decimal_places=2)
    itemvalue = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    loanamount = models.PositiveIntegerField()
    interestrate = models.PositiveSmallIntegerField(default=2)
    interest = models.PositiveIntegerField()

    series = models.ForeignKey(
        "girvi.Series",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    posted = models.BooleanField(default=False)
    journals = GenericRelation(Journal, related_query_name="loan_doc")
    # notifications = models.ManyToManyField(Notification)
    # Managers
    # objects = LoanManager.from_queryset(LoanQuerySet)()
    objects = LoanManager()
    released = ReleasedManager()
    unreleased = UnReleasedManager()
    lqs = LoanQuerySet.as_manager()

    class Meta:
        ordering = ("series", "lid")

    def __str__(self):
        return f"{self.loanid} - {self.loanamount} - {self.created.date()}"

    def get_absolute_url(self):
        return reverse("girvi_loan_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("girvi_loan_update", args=(self.pk,))

    def noofmonths(self, date=datetime.datetime.now(timezone.utc)):
        cd = date  # datetime.datetime.now()
        nom = (cd.year - self.created.year) * 12 + cd.month - self.created.month
        return 1 if nom <= 0 else nom - 1

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

    def interest_amt(self):
        return round(Decimal(self.loanamount * (self.interestrate) / 100), 3)

    def interestdue(self, date=datetime.datetime.now(timezone.utc)):
        if self.is_released:
            return Decimal(0)
        else:
            return self.interest_amt() * self.noofmonths(date)

    def total(self):
        return self.interestdue() + self.loanamount

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

    def due(self):
        a = self.get_total_adjustments()
        return self.loanamount + self.interestdue() - a["int"] - a["amt"]

    def is_worth(self):
        rate = Rate.objects.latest("timestamp")
        return ((self.itemweight * 75) / 100) * rate.buying_rate < self.total()

    def get_next(self):
        return (
            Loan.objects.filter(series=self.series, lid__gt=self.lid)
            .order_by("lid")
            .first()
        )

    def get_previous(self):
        return (
            Loan.objects.filter(series=self.series, lid__lt=self.lid)
            .order_by("lid")
            .last()
        )

    @transaction.atomic()
    def post(self):
        # get contact.Account
        try:
            self.customer.account
        except:
            self.customer.save()
        amount = Money(self.loanamount, "INR")
        interest = Money(self.interest_amt(), "INR")
        if self.customer.type == "Su":
            print(self.customer.type)
            jrnl = Journal.objects.create(
                type=JournalTypes.LT, content_object=self, desc="Loan Taken"
            )
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
            jrnl = Journal.objects.create(
                type=JournalTypes.LG, content_object=self, desc="Loan Given"
            )
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
        jrnl.transact(lt, at)

        self.posted = True
        self.save(update_fields=["posted"])

    @transaction.atomic()
    def unpost(self):
        # delete journals if accounts and ledger not closed
        last_jrnl = self.journals.latest()
        if self.customer.type == "Su":
            l_jrnl = Journal.objects.create(
                content_object=self, desc="Loan Taken Revert"
            )
        else:
            l_jrnl = Journal.objects.create(
                content_object=self, desc="Loan Given Revert"
            )
        l_jrnl.untransact(last_jrnl)
        # i_jrnl.untransact()
        self.posted = False
        self.save(update_fields=["posted"])

    def save(self, *args, **kwargs):
        if not self.pk:
            self.itemvalue = self.loanamount + 500
        self.loanid = self.series.name + str(self.lid)
        self.interest = self.interestdue()
        super().save(*args, **kwargs)
        return self

    @property
    def last_notified(self):
        notice = self.notification_set.last()
        return notice


class LoanItem(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    item = models.ForeignKey(
        "product.ProductVariant", on_delete=models.SET_NULL, null=True
    )
    # class Itemtype(models.TextChoices):
    #     G = "Gold"
    #     S = "Silver"
    #     B = "Bronze"

    # itemtype = models.CharField(
    #     max_length=20, choices=Itemtype.choices, default=Itemtype.G
    # )
    # item = models.CharField(max_length=20)
    qty = models.PositiveIntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=3)

    loanamount = models.DecimalField(max_digits=10, decimal_places=2)
    interestrate = models.DecimalField(max_digits=10, decimal_places=2)
    interest = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.item} - {self.qty}"

    def get_absolute_url(self):
        return reverse("girvi_loanitem_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("girvi_loanitem_update", args=(self.pk,))

    def update_loan(self):
        pass


class Adjustment(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, null=True, blank=True
    )
    amount_received = models.IntegerField(default=0)
    as_interest = models.BooleanField(default=True)
    posted = models.BooleanField(default=False)

    loan = models.ForeignKey(
        "girvi.Loan", on_delete=models.CASCADE, related_name="adjustments"
    )
    journals = GenericRelation(Journal, related_query_name="loan_adjustment_doc")

    class Meta:
        ordering = ("created",)

    def __str__(self):
        return f"{self.amount_received}=>loan{self.loan}"

    def get_absolute_url(self):
        return reverse("girvi_adjustment_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("girvi_adjustments_update", args=(self.pk,))

    # correct the transactions
    def post(self):
        amount = Money(self.amount_received, "INR")
        interest = 0 if not self.as_interest else Money(self.amount_received, "INR")
        if self.customer.type == "Su":
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
        jrnl.transact(lt, at)

        self.posted = True
        self.save(update_fields=["posted"])

    def unpost(self):
        last_jrnl = self.journals.latest()
        if self.loan.customer.type == "Su":
            jrnl = Journal.objects.create(
                content_object=self, desc="Loan Adjustment Revert"
            )
        else:
            jrnl = Journal.objects.create(
                content_object=self, desc="Loan Adjustment Revert"
            )
        jrnl.untransact(last_jrnl)
        self.posted = False
        self.save(update_fields="posted")


class LoanStatement(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, null=True, blank=True
    )
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.created}"
