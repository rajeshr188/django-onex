from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce


class StockManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related("variant")


class StockLotManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related("variant")
