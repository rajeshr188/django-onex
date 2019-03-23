from .models import Invoice,Receipt
from contact.models import Customer
import django_filters
from django_select2.forms import Select2Widget

class InvoiceFilter(django_filters.FilterSet):
    customer=django_filters.ModelChoiceFilter(
                    queryset=Customer.objects.filter(type = 'Wh'),widget=Select2Widget)
    class Meta:
        model=Invoice
        fields=['id','paymenttype','balancetype','status']

class ReceiptFilter(django_filters.FilterSet):
    customer=django_filters.ModelChoiceFilter(
                    queryset=Customer.objects.all(),widget=Select2Widget)
    class Meta:
        model=Receipt
        fields=['id','created','type','status']
