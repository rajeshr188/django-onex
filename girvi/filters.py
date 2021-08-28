from .models import Loan, LoanStatement,Release,Adjustment
from contact.models import Customer
import django_filters
from django_select2.forms import Select2Widget

class LoanFilter(django_filters.FilterSet):
    loanid=django_filters.CharFilter(lookup_expr='icontains')
    itemdesc=django_filters.CharFilter(lookup_expr='icontains')
    customer=django_filters.ModelChoiceFilter(
                    queryset = Customer.objects.filter(type='Re',active = True),
                    widget=Select2Widget)
    Status = django_filters.BooleanFilter(field_name='release', method='filter_status')

    def filter_status(self,queryset,name,value):
        return queryset.filter(release__isnull=value)
    class Meta:
        model=Loan
        fields=['loanid','series','customer','itemtype','itemweight','itemdesc','loanamount']

class LoanStatementFilter(django_filters.FilterSet):
    loan = django_filters.ModelChoiceFilter(
        widget = Select2Widget,
        queryset = Loan.objects.filter(series__is_active = True)
    )
    class Meta:
        model = LoanStatement
        fields = ['loan']

class AdjustmentFilter(django_filters.FilterSet):
    class Meta:
        model = Adjustment
        fields = ['loan']

class ReleaseFilter(django_filters.FilterSet):
    class Meta:
        model = Release
        fields = ['releaseid','loan']
