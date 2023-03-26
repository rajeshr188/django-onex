from decimal import Decimal

import django_filters
from django.db.models import Q
from django.forms.widgets import CheckboxInput, RadioSelect

from .models import Customer


class CustomerFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")
    relatedto = django_filters.CharFilter(lookup_expr="icontains")
    # contactno = django_filters.CharFilter(
    #     field_name="contactno__phone_number", lookup_expr="icontains"
    # )

    class Meta:
        model = Customer
        fields = [
            "query",
            "relatedto",
            "customer_type",
            "active",
        ]

    def universal_search(self, queryset, name, value):
        # if value.replace(".", "", 1).isdigit():
        #     value = Decimal(value)
        #     return Customer.objects.filter(
        #         Q(price=value) | Q(cost=value)
        #     )

        return Customer.objects.filter(
            Q(name__icontains=value)
            | Q(id__icontains=value)
            | Q(contactno__phone_number__icontains=value)
        )
