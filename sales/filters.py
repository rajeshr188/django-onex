from .models import Invoice,Receipt
from contact.models import Customer
import django_filters
from django_select2.forms import Select2Widget

class InvoiceFilter(django_filters.FilterSet):
    customer=django_filters.ModelChoiceFilter(
                    queryset=Customer.objects.exclude(type = 'Re'),widget=Select2Widget)
    due_date = django_filters.DateFilter(field_name='due_date',lookup_expr='lte')
    class Meta:
        model=Invoice
        fields=['id','balancetype','status']

class ReceiptFilter(django_filters.FilterSet):
    customer=django_filters.ModelChoiceFilter(
                    queryset=Customer.objects.all(),widget=Select2Widget)
    class Meta:
        model=Receipt
        fields=['id','created','type','status']
