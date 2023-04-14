import django_filters
from django_select2.forms import Select2Widget

from contact.forms import CustomerWidget
from contact.models import Customer

from .models import Invoice, Payment


class InvoiceFilter(django_filters.FilterSet):
    supplier = django_filters.ModelChoiceFilter(
        queryset=Customer.objects.all(),
        # widget=Select2Widget creates N=1 problem with customer contacts
        widget=CustomerWidget,
    )
    created = django_filters.DateTimeFromToRangeFilter()
    posted = django_filters.BooleanFilter(field_name="posted", lookup_expr="isnull")

    class Meta:
        model = Invoice
        fields = ["id", "created", "is_gst", "balancetype", "status", "posted"]


class PaymentFilter(django_filters.FilterSet):
    supplier = django_filters.ModelChoiceFilter(
        queryset=Customer.objects.all(), widget=Select2Widget
    )

    class Meta:
        model = Payment
        fields = ["id", "created", "payment_type", "status"]
