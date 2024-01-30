import datetime

from django.db import models
from django.db.models import (BooleanField, Case, DecimalField,
                              ExpressionWrapper, F, FloatField, Func, Q, Sum,
                              Value, When)
from django.db.models.functions import (Coalesce, ExtractMonth, ExtractYear,
                                        Round)
from django.utils import timezone

from product.models import Rate, RateSource
from polymorphic.managers import PolymorphicManager
"""
    each row shall have
        itemwise weight
        itemwise pure_weight
        itemwise loanamount
        no_of_months
        total_interest
        due
        current_value
        is_overdue
    total weight,pureweight,itemwise_loanamount,loanamount,currentvalue,itemwise currentvalue

"""


class LoanQuerySet(models.QuerySet):
    def released(self):
        return self.filter(release__isnull=False)

    def unreleased(self):
        return self.filter(release__isnull=True)

    def with_total_interest(self):
        today = datetime.date.today()

        return self.annotate(
            no_of_months=ExpressionWrapper(
                today.month
                - F("created__month")
                + 12 * (today.year - F("created__year")),
                output_field=DecimalField(decimal_places=2),
            ),
            loan_interest=F("interest") * F("no_of_months"),
        ).aggregate(Sum("loan_interest"))

    # def with_due(self):
    #     current_time = timezone.now()
    #     return self.annotate(
    #         months_since_created=ExpressionWrapper(
    #             Func(
    #                 (ExtractYear(current_time) - ExtractYear(F("created"))) * 12
    #                 + (ExtractMonth(current_time) - ExtractMonth(F("created")))
    #                 + (current_time.day - F("created__day")) / 30,
    #                 function="ROUND",
    #             ),
    #             output_field=models.FloatField(),
    #         ),
    #         total_interest = ExpressionWrapper(
    #             Func(
    #                 (F("interest") * F("months_since_created")),
    #                 function="ROUND",
    #             ),
    #             output_field=models.FloatField(),
    #         ),
    #         total_due=F("loanamount") + F("total_interest"),
    #     )

    # def with_is_overdue(self):
    #     is_overdue = Case(
    #         When(total_due__gt=F("current_value"), then=True),
    #         default=False,
    #         output_field=BooleanField(),
    #     )
    #     return self.annotate(is_overdue=is_overdue)

    # def with_current_value(self):
    #     latest_gold_rate = Rate.objects.filter(metal=Rate.Metal.GOLD).order_by("-timestamp").first()
    #     latest_silver_rate = Rate.objects.filter(metal=Rate.Metal.SILVER).order_by("-timestamp").first()

    #     return self.annotate(
    #         current_value=Round(Sum(
    #             Case(
    #                 When(loanitems__itemtype='Gold', then=F('loanitems__weight') * latest_gold_rate.buying_rate * 0.75
    #                       if latest_gold_rate is not None
    #                       else Value(0)),
    #                 When(loanitems__itemtype='Silver', then=F('loanitems__weight') * latest_silver_rate.buying_rate * 0.75
    #                       if latest_silver_rate is not None
    #                       else Value(0)),
    #                 default=Value(0),
    #                 output_field=models.DecimalField(max_digits=10, decimal_places=2)
    #             )
    #         ))
    #     )

    # def with_weight(self):
    #     return self.annotate(
    #         total_gold_weight=Sum(
    #             Case(
    #                 When(loanitems__itemtype='Gold', then=F('loanitems__weight')),
    #                 default=Value(0),
    #                 output_field=models.DecimalField(max_digits=10, decimal_places=2)
    #             )
    #         ),
    #         total_silver_weight=Sum(
    #             Case(When(loanitems__itemtype='Silver', then=F('loanitems__weight')),
    #             default=Value(0),
    #             output_field=models.DecimalField(max_digits=10, decimal_places=2))),
    #     )

    # def with_pure_weight(self):
    #     return self.annotate(
    #         pure_gold_weight=Sum(
    #             Case(
    #                 When(loanitems__itemtype='Gold', then=F('loanitems__weight')*F('loanitems__purity')),
    #                 default=Value(0),
    #                 output_field=models.DecimalField(max_digits=10, decimal_places=2)
    #             )
    #         ),
    #         pure_silver_weight=Sum(
    #             Case(When(loanitems__itemtype='Silver', then=F('loanitems__weight')*F('loanitems__purity')),
    #             default=Value(0),
    #             output_field=models.DecimalField(max_digits=10, decimal_places=2))),
    #     )

    def with_details(self):
        current_time = timezone.now()
        latest_gold_rate = (
            Rate.objects.filter(metal=Rate.Metal.GOLD).order_by("-timestamp").first()
        )
        latest_silver_rate = (
            Rate.objects.filter(metal=Rate.Metal.SILVER).order_by("-timestamp").first()
        )
        return self.annotate(
            months_since_created=ExpressionWrapper(
                Func(
                    (ExtractYear(current_time) - ExtractYear(F("created_at"))) * 12
                    + (ExtractMonth(current_time) - ExtractMonth(F("created_at")))
                    + (current_time.day - F("created_at__day")) / 30,
                    function="ROUND",
                ),
                output_field=models.FloatField(),
            ),
            total_interest=ExpressionWrapper(
                Func(
                    (F("interest") * F("months_since_created")),
                    function="ROUND",
                ),
                output_field=models.FloatField(),
            ),
            total_due=F("loanamount") + F("total_interest"),
            total_gold_weight=Sum(
                Case(
                    When(loanitems__itemtype="Gold", then=F("loanitems__weight")),
                    default=Value(0),
                    output_field=models.DecimalField(max_digits=10, decimal_places=2),
                )
            ),
            total_silver_weight=Sum(
                Case(
                    When(loanitems__itemtype="Silver", then=F("loanitems__weight")),
                    default=Value(0),
                    output_field=models.DecimalField(max_digits=10, decimal_places=2),
                )
            ),
            total_bronze_weight=Sum(
                Case(
                    When(loanitems__itemtype="Bronze", then=F("loanitems__weight")),
                    default=Value(0),
                    output_field=models.DecimalField(max_digits=10, decimal_places=2),
                )
            ),
            pure_gold_weight=Sum(
                Case(
                    When(
                        loanitems__itemtype="Gold",
                        then=F("loanitems__weight") * F("loanitems__purity") * 0.01,
                    ),
                    default=Value(0),
                    output_field=models.DecimalField(max_digits=10, decimal_places=2),
                )
            ),
            pure_silver_weight=Sum(
                Case(
                    When(
                        loanitems__itemtype="Silver",
                        then=F("loanitems__weight") * F("loanitems__purity") * 0.01,
                    ),
                    default=Value(0),
                    output_field=models.DecimalField(max_digits=10, decimal_places=2),
                )
            ),
            pure_bronze_weight=Sum(
                Case(
                    When(
                        loanitems__itemtype="Bronze",
                        then=F("loanitems__weight") * F("loanitems__purity") * 0.01,
                    ),
                    default=Value(0),
                    output_field=models.DecimalField(max_digits=10, decimal_places=2),
                )
            ),
            current_value=Round(
                ExpressionWrapper(
                    (F("pure_gold_weight") * latest_gold_rate.buying_rate)
                    + (F("pure_silver_weight") * latest_silver_rate.buying_rate),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )
            ),
            is_overdue=Case(
                When(total_due__gt=F("current_value"), then=True),
                default=False,
                output_field=BooleanField(),
            ),
            worth=ExpressionWrapper(
                F("current_value") - F("total_due"), output_field=DecimalField()
            ),
        )

    def with_itemwise_loanamount(self):
        return self.annotate(
            total_gold_la=Sum(
                Case(
                    When(loanitems__itemtype="Gold", then=F("loanitems__loanamount")),
                    default=Value(0),
                    output_field=models.DecimalField(max_digits=10, decimal_places=2),
                )
            ),
            total_silver_la=Sum(
                Case(
                    When(loanitems__itemtype="Silver", then=F("loanitems__loanamount")),
                    default=Value(0),
                    output_field=models.DecimalField(max_digits=10, decimal_places=2),
                )
            ),
            total_bronze_la=Sum(
                Case(
                    When(loanitems__itemtype="Bronze", then=F("loanitems__loanamount")),
                    default=Value(0),
                    output_field=models.DecimalField(max_digits=10, decimal_places=2),
                )
            ),
            total_la=F("total_gold_la") + F("total_silver_la") + F("total_bronze_la"),
        )

    def total_itemwise_loanamount(self):
        return self.aggregate(
            gold_loanamount=Sum("total_gold_la"),
            silver_loanamount=Sum("total_silver_la"),
            bronze_loanamount=Sum("total_bronze_la"),
        )

    def total_current_value(self):
        return self.aggregate(total=Sum("current_value"))

    def total_weight(self):
        return self.aggregate(
            gold=Sum("total_gold_weight"),
            silver=Sum("total_silver_weight"),
            bronze=Sum("total_bronze_weight"),
        )

    def total_pure_weight(self):
        return self.aggregate(
            gold=Round(Sum("pure_gold_weight"), 2),
            silver=Round(Sum("pure_silver_weight"), 2),
            bronze=Round(Sum("pure_bronze_weight")),
        )

    def itemwise_value(self):
        latest_gold_rate = (
            Rate.objects.filter(metal=Rate.Metal.GOLD).order_by("-timestamp").first()
        )
        latest_silver_rate = (
            Rate.objects.filter(metal=Rate.Metal.SILVER).order_by("-timestamp").first()
        )
        return self.aggregate(
            gold=Round(Sum("pure_gold_weight") * latest_gold_rate.buying_rate, 2),
            silver=Round(Sum("pure_silver_weight") * latest_silver_rate.buying_rate, 2),
        )

    def total_loanamount(self):
        return self.aggregate(total=Sum("loanamount"))


class LoanManager(PolymorphicManager):
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

    def with_details(self):
        return self.get_queryset().with_details()

    def with_itemwise_loanamount(self):
        return self.get_queryset().with_itemwise_loanamount()

    def total_itemwise_loanamount(self):
        return self.get_queryset().total_itemwise_loanamount()

    def with_total_value(self):
        return self.get_queryset().aggregate(total_value=Sum("current_value"))

    def total_loanamount(self):
        return self.get_queryset().aggregate(total=Sum("loanamount"))

    def total_weight(self):
        return self.get_queryset().total_weight()

    def total_pure_weight(self):
        return self.get_queryset().total_pure_weight()

    # def with_due(self):
    #     return self.get_queryset().with_due()

    # def with_is_overdue(self):
    #     return self.get_queryset().with_is_overdue()

    # def with_weight(self):
    #     # Calculate the weight of each loanitem by itemtype on each row
    #     return self.annotate(
    #         gold_weight=Sum(
    #                         Case(
    #                             When(
    #                                 loanitems__itemtype='Gold', then=F('loanitems__weight')
    #                                 ), default=Value(0),
    #                                 output_field=DecimalField(max_digits=10, decimal_places=2))),
    #         silver_weight=Sum(Case(When(loanitems__itemtype='Silver', then=F('loanitems__weight')), default=Value(0), output_field=DecimalField(max_digits=10, decimal_places=2))),
    #         # Add more itemtypes as needed
    #     )

    # def with_total_weight(self):
    #     # Calculate the total weight for each itemtype across all loans
    #     return self.aggregate(
    #         total_gold_weight=Sum('loanitems__weight', filter=Q(loanitems__itemtype='Gold'), output_field=DecimalField(max_digits=10, decimal_places=2)),
    #         total_silver_weight=Sum('loanitems__weight', filter=Q(loanitems__itemtype='Silver'), output_field=DecimalField(max_digits=10, decimal_places=2)),
    #         # Add more itemtypes as needed
    #     )
    # def with_total_pure_weight(self):
    #     return self.aggregate(
    #         pure_gold = Sum("pure_gold_weight"),
    #         pure_silver = Sum("pure_silver_weight")
    #     )

    # def with_weight(self):
    #     return self.get_queryset().with_weight()

    # def with_total_weight(self):
    #     return self.get_queryset().with_weight().aggregate(
    #         gold = Sum("total_gold_weight"),
    #         silver = Sum("total_silver_weight")
    #     )


class ReleasedManager(PolymorphicManager):
    def get_queryset(self):
        return super().get_queryset().filter(release__isnull=False)


class UnReleasedManager(PolymorphicManager):
    def get_queryset(self):
        return super().get_queryset().filter(release__isnull=True)
