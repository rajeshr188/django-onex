from datetime import date

from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone


class PurchaseQueryset(models.QuerySet):
    def gst(self):
        return self.filter(is_gst=True)

    def non_gst(self):
        return self.filter(is_gst=False)

    def total(self):
        return self.aggregate(
            cash=Sum("balance", filter=Q(balancetype="INR")),
            gold=Sum("balance", filter=Q(balancetype="USD")),
            silver=Sum("balance", filter=Q(balancetype="AUD")),
        )

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
