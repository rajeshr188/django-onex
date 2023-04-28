from datetime import date

from django.db import models
from django.db.models import F, Q, Sum
from django.utils import timezone


class PurchaseQueryset(models.QuerySet):
    def is_gst(self, value):
        return self.filter(is_gst=value)

    def is_ratecut(self, value):
        return self.filter(is_ratecut=value)

    def today(self):
        return self.filter(created__date=date.today())

    def cur_month(self):
        return self.filter(
            created__month=date.today().month, created__year=date.today().year
        )

    def total_with_ratecut(self):
        return self.aggregate(
            cash=Sum("balance", filter=Q(balancetype="INR")),
            cash_g=Sum("balance", filter=Q(balancetype="INR", metaltype="Gold")),
            cash_s=Sum("balance", filter=Q(balancetype="INR", metaltype="Silver")),
            cash_g_nwt=Sum("net_wt", filter=Q(balancetype="INR", metaltype="Gold")),
            cash_s_nwt=Sum("net_wt", filter=Q(balancetype="INR", metaltype="Silver")),
            gold=Sum("balance", filter=Q(balancetype="USD")),
            silver=Sum("balance", filter=Q(balancetype="AUD")),
        )

    def with_balance(self):
        return self.annotate(
            gold_balance=Sum(
                "purchaseitem__metal_balance", filter=Q(metal_balance_currency="USD")
            ),
            silver_balance=Sum(
                "purchaseitem__metal_balance", filter=Q(metal_balance_currency="EUR")
            ),
            cash_balance=Sum("purchaseitem__cash_balance"),
        ).select_related("purchaseitem")

    def with_allocated_payment(self):
        return self.annotate(
            gold_amount=Sum(
                "paymentallocation__allocated",
                filter=Q(paymentallocation__allocated_currency="USD"),
            ),
            silver_amount=Sum(
                "paymentallocation__allocated",
                filter=Q(paymentallocation__allocated_currency="EUR"),
            ),
            cash_amount=Sum(
                "paymentallocation__allocated",
                filter=Q(paymentallocation__allocated_currency="INR"),
            ),
        ).select_related("paymentallocation")

    def with_outstanding_balance(self):
        return self.annotate(
            outstanding_gold_balance=F("gold_amount") - F("gold_balance"),
            outstanding_silver_balance=F("silver_amount") - F("silver_balance"),
            outstanding_cash_balance=F("cash_amount") - F("cash_balance"),
        )
