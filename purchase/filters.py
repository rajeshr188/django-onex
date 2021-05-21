from .models import Invoice,Payment
from contact.models import Customer
import django_filters
from django_select2.forms import Select2Widget

class InvoiceFilter(django_filters.FilterSet):
    supplier=django_filters.ModelChoiceFilter(
                    queryset=Customer.objects.all(),widget=Select2Widget)
    created=django_filters.DateTimeFromToRangeFilter()
    class Meta:
        model=Invoice
        fields=['id','created','is_gst','paymenttype','balancetype','status']

class PaymentFilter(django_filters.FilterSet):
    supplier=django_filters.ModelChoiceFilter(
                    queryset=Customer.objects.all(),widget=Select2Widget)

    class Meta:
        model=Payment
        fields=['id','created','type','status']
