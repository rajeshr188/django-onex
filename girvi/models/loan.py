import math
from datetime import datetime
from decimal import Decimal
# from qrcode.image.pure import PyImagingImage
from io import BytesIO

import qrcode
import qrcode.image.svg
from dateutil.relativedelta import relativedelta
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.db.models import (BooleanField, Case, DecimalField,
                              ExpressionWrapper, F, Func, Q, Sum, Value, When)
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear
from django.urls import reverse
from django.utils import timezone
from moneyed import Money

from contact.models import Customer
from dea.models import JournalEntry  # , JournalTypes
from dea.models import Journal
from rates.models import Rate

from ..managers import (LoanManager, LoanQuerySet, ReleasedManager,
                        UnReleasedManager)


class Loan(models.Model):
    # Fields
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, null=True, blank=True
    )
    loan_date = models.DateTimeField(default=datetime.now)
    lid = models.IntegerField(blank=True, null=True)
    loan_id = models.CharField(max_length=255, unique=True, db_index=True)
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
    # ----------redundant fields
    item_desc = models.TextField(
        max_length=100,
        verbose_name="Item",
        blank=True,
        null=True,
    )
    loan_amount = models.PositiveIntegerField(
        verbose_name="Amount", default=0, null=True, blank=True
    )

    interest = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, null=True, blank=True
    )
    # -----------------------------------
    series = models.ForeignKey(
        "girvi.Series",
        on_delete=models.CASCADE,
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    # journal_entries = GenericRelation(JournalEntry, related_query_name="loan_doc")
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
        return f"{self.loan_id} - {self.loan_amount} - {self.loan_date.date()}"

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

    @property
    def last_notified(self):
        notice = self.notification_set.last()
        return notice

    # function to get no of months since loan was taken

    def get_loanamount(self):
        payments = (
            self.loan_payments.aggregate(Sum("payment_amount"))["payment_amount__sum"]
            or 0
        )
        items_total = (
            self.loanitems.aggregate(Sum("loanamount"))["loanamount__sum"] or 0
        )
        return items_total - payments

    def get_total_payments(self):
        total_payments = self.loan_payments.aggregate(Sum("payment_amount"))[
            "payment_amount__sum"
        ]
        return total_payments or 0

    def get_total_interest_payments(self):
        return (
            self.loan_payments.aggregate(Sum("interest_payment"))[
                "interest_payment__sum"
            ]
            or 0
        )

    def get_total_principal_payments(self):
        return (
            self.loan_payments.aggregate(Sum("principal_payment"))[
                "principal_payment__sum"
            ]
            or 0
        )

    def noofmonths(self, date=None):
        if date is None:
            date = datetime.now(timezone.utc)
        nom = relativedelta(date, self.loan_date)
        return nom.years * 12 + nom.months

    def interestdue(self, date=datetime.now(timezone.utc)):
        return round(self.interest * self.noofmonths(date))

    def current_value(self):
        total_current_value = sum(
            loan_item.current_value() for loan_item in self.loanitems.all()
        )
        return total_current_value

    def total(self):
        return self.interestdue() + self.loan_amount

    def due(self):
        # a = self.get_total_adjustments()
        payment = (
            self.loan_payments.aggregate(Sum("payment_amount"))["payment_amount__sum"]
            or 0
        )
        return self.loan_amount + self.interestdue() - payment

    def is_worth(self):
        return self.current_value() < self.total()

    def get_worth(self):
        return self.current_value() - self.total()

    def calculate_months_to_exceed_value(self):
        try:
            if not self.is_released and self.loanitems.exists():
                return math.ceil((self.current_value() - self.total()) / self.interest)
        except Exception as e:
            return 0
        return 0

    def create_release(self, release_date, released_by, created_by):
        from girvi.models import Release

        release = Release.objects.create(
            loan=self,
            release_date=release_date,
            released_by=released_by,
            created_by=created_by,
        )
        release.save()
        return release

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

    def get_transactions(self):
        try:
            self.customer.account
        except:
            self.customer.save()
        amount = Money(self.loan_amount, "INR")
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
        self.loan_id = self.series.name + str(self.lid)
        super(Loan, self).save(*args, **kwargs)

    def update(self):
        try:
            self.interest = (
                sum(loan_item.interest for loan_item in self.loanitems.all())
                - self.get_total_interest_payments()
            )
            self.loan_amount = (
                sum(loan_item.loanamount for loan_item in self.loanitems.all())
                - self.get_total_principal_payments()
            )

            with transaction.atomic():
                super(Loan, self).save()
        except Exception as e:
            # Handle or log the error as needed
            print(f"An error occurred while updating the loan: {e}")

    def notify(self, notice_type, medium_type):
        from notify.models import Notification

        notification = Notification(
            loan=self, notice_type=notice_type, medium_type=medium_type
        )
        notification.save()
        return notification


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
        self.loan.update()

    def delete(self, *args, **kwargs):
        loan = self.loan
        super(LoanItem, self).delete(*args, **kwargs)
        loan.update()


class LoanPayment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, null=True, blank=True
    )
    loan = models.ForeignKey(
        "Loan", on_delete=models.CASCADE, related_name="loan_payments"
    )
    payment_date = models.DateTimeField()
    payment_amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Payment"
    )
    principal_payment = models.DecimalField(max_digits=10, decimal_places=2)
    interest_payment = models.DecimalField(max_digits=10, decimal_places=2)
    # journal_entries = GenericRelation(
    #     JournalEntry, related_query_name="loan_payment_doc"
    # )
    with_release = models.BooleanField(default=False)

    class Meta:
        ordering = ("-id",)

    def __str__(self):
        return f"{self.loan.loan_id} - {self.payment_date} - {self.payment_amount}"

    def get_absolute_url(self):
        return reverse("girvi:girvi_loanpayment_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("girvi:girvi_loanpayment_update", args=(self.pk,))

    def save(self, *args, **kwargs):
        interest_payment = min(self.payment_amount, self.loan.interestdue())
        principal_payment = self.payment_amount - interest_payment
        self.principal_payment = principal_payment
        self.interest_payment = interest_payment
        super(LoanPayment, self).save(*args, **kwargs)
        self.loan.update()
        # if self.with_release and not self.loan.is_released:
        #     release = self.loan.create_release(self.payment_date, self.loan.customer, self.created_by)

    def delete(self, *args, **kwargs):
        loan = self.loan
        super(LoanPayment, self).delete(*args, **kwargs)
        loan.update()
        if self.with_release and self.loan.is_released:
            self.loan.release.delete()

    def get_transactions(self):
        amount = Money(self.payment_amount, "INR")
        interest = Money(self.interest_payment, "INR")
        principal = Money(self.principal_payment, "INR")
        if self.loan.loan_type == self.loan.LoanType.TAKEN:
            lt = [
                {"ledgerno": "Cash", "ledgerno_dr": "Loans", "amount": principal},
                {
                    "ledgerno": "Cash",
                    "ledgerno_dr": "Interest Paid",
                    "amount": interest,
                },
            ]
            at = [
                {
                    "ledgerno": "Loans",
                    "xacttypecode": "Cr",
                    "xacttypecode_ext": "LP",
                    "account": self.loan.customer.account,
                    "amount": principal,
                },
                {
                    "ledgerno": "Interest Payable",
                    "xacttypecode": "Cr",
                    "xacttypecode_ext": "IP",
                    "account": self.loan.customer.account,
                    "amount": interest,
                },
            ]
        else:
            lt = [
                {
                    "ledgerno": "Loans & Advances",
                    "ledgerno_dr": "Cash",
                    "amount": principal,
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
                    "xacttypecode_ext": "LR",
                    "account": self.loan.customer.account,
                    "amount": principal,
                },
                {
                    "ledgerno": "Interest Received",
                    "xacttypecode": "Dr",
                    "xacttypecode_ext": "IR",
                    "account": self.loan.customer.account,
                    "amount": interest,
                },
            ]
        return lt, at


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
