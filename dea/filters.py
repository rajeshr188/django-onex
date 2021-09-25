import django_filters
from .models import AccountType_Ext, Accountbalance, Ledgerbalance
from django_select2.forms import Select2Widget

class AccountFilter(django_filters.FilterSet):

    acc_name = django_filters.CharFilter(lookup_expr='icontains')
    acc_type = django_filters.ModelChoiceFilter(
        queryset=AccountType_Ext.objects.all(),
        widget=Select2Widget,
        field_name='acc_type', method='filter_acc_type')

    def filter_acc_type(self, queryset, name, value):
        return queryset.filter(acc_type=value)
    
    class Meta:
        model = Accountbalance
        fields =['acc_type','acc_name',]

class LedgerFilter(django_filters.FilterSet):
    class Meta:
        model = Ledgerbalance
        fields = ['ledgerno','name']
