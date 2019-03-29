from .models import Loan,Release
from contact.models import Customer
import django_filters
from django_select2.forms import Select2Widget

class LoanFilter(django_filters.FilterSet):
    loanid=django_filters.CharFilter(lookup_expr='icontains')
    customer=django_filters.ModelChoiceFilter(
                    queryset=Customer.objects.filter(type = 'Re'),widget=Select2Widget)
    class Meta:
        model=Loan
        fields=['loanid','license','customer','itemtype','license']

class ReleaseFilter(django_filters.FilterSet):
    customer = django_filters.ModelChoiceFilter(
                    queryset = Customer.objects.filter(type='Re'),widget = Select2Widget)
    class Meta:
        model = Release
        fields = ['releaseid','customer','loan']
