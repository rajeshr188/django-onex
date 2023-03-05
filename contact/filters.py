import django_filters
from .models import Customer


class CustomerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    relatedto = django_filters.CharFilter(lookup_expr="icontains")
    contactno = django_filters.CharFilter(
        field_name="contactno__number", lookup_expr="icontains"
    )

    class Meta:
        model = Customer
        fields = ["id", "name", "relatedto", "type", "active"]
