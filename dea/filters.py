import django_filters
from django.db.models import Q

from .models import Ledger


class LedgerTransactionFilter(django_filters.FilterSet):
    created = django_filters.DateFromToRangeFilter()
    ledgerno = django_filters.ModelChoiceFilter(
        queryset=Ledger.objects.all(), label="Credit"
    )
    ledgerno_dr = django_filters.ModelChoiceFilter(
        queryset=Ledger.objects.all(), label="Debit"
    )

    class Meta:
        model = Ledger
        fields = ["created", "ledgerno", "ledgerno_dr"]
