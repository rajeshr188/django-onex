import datetime

from django.db import models
from django.db.models import (
    BooleanField,
    Case,
    DecimalField,
    ExpressionWrapper,
    F,
    Func,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear
from django.utils import timezone

from product.models import Rate, RateSource


class LoanQuerySet(models.QuerySet):
    def released(self):
        return self.filter(release__isnull=False)

    def unreleased(self):
        return self.filter(release__isnull=True)

    def with_due(self):
        current_time = timezone.now()
        return self.annotate(
            months_since_created=ExpressionWrapper(
                Func(
                    (ExtractYear(current_time) - ExtractYear(F("created"))) * 12
                    + (ExtractMonth(current_time) - ExtractMonth(F("created")))
                    + (current_time.day - F("created__day")) / 30,
                    function="ROUND",
                ),
                output_field=models.FloatField(),
            ),
            total_loanamount=Sum("loanamount"),
            total_interest=ExpressionWrapper(
                Func(
                    (F("loanamount") * F("interestrate") * F("months_since_created"))
                    / 100,
                    function="ROUND",
                ),
                output_field=models.FloatField(),
            ),
            total_due=F("loanamount") + F("total_interest"),
        )

    def with_current_value(self):
        latest_gold_rate = (
            Rate.objects.filter(metal=Rate.Metal.GOLD).latest("timestamp").buying_rate
        )
        latest_silver_rate = (
            Rate.objects.filter(metal=Rate.Metal.SILVER).latest("timestamp").buying_rate
        )

        return self.annotate(
            current_value=ExpressionWrapper(
                Case(
                    When(
                        itemtype="Gold", then=F("itemweight") * latest_gold_rate * 0.75
                    ),
                    When(
                        itemtype="Silver",
                        then=F("itemweight") * latest_silver_rate * 0.70,
                    ),
                    default=Value(0),
                    output_field=models.FloatField(),
                ),
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
        ).aggregate(Sum("loan_interest"))

    def with_weight(self):
        return self.aggregate(
            gold_wt=Sum("itemweight", filter=Q(itemtype="Gold")),
            silver_wt=Sum("itemweight", filter=Q(itemtype="Silver")),
            bronze_wt=Sum("itemweight", filter=Q(itemtype="Bronze")),
        )


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

    def with_due(self):
        return self.get_queryset().with_due()

    def with_current_value(self):
        return self.get_queryset().with_current_value()

    def with_is_overdue(self):
        return self.get_queryset().with_is_overdue()

    def with_weight(self):
        return self.get_queryset().with_weight()


class ReleasedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(release__isnull=False)


class UnReleasedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(release__isnull=True)
