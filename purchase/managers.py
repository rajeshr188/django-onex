from datetime import date

from django.db import models
from django.db.models import F, Q, Sum
from django.utils import timezone
from polymorphic.query import PolymorphicQuerySet


class PurchaseQueryset(PolymorphicQuerySet):
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
                "purchase_items__metal_balance",
                filter=Q(purchase_items__metal_balance_currency="USD"),
            ),
            silver_balance=Sum(
                "purchase_items__metal_balance",
                filter=Q(purchase_items__metal_balance_currency="EUR"),
            ),
            cash_balance=Sum("purchase_items__cash_balance"),
        ).select_related("purchase_items")

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

    # def delete(self):
    #     # add custom logic here
    #     # for example, check if any of the objects can be deleted
    #     deletable_objects = [obj for obj in self if obj.can_be_deleted()]
    #     if deletable_objects:
    #         # call the parent's delete method to actually delete the objects
    #         super(MyModelQuerySet, deletable_objects).delete()
    #     else:
    #         # raise an exception or return a message to indicate that deletion is not allowed
    #         raise Exception("Deletion not allowed for any of the objects")
