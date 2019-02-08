from .models import Loan
import django_filters

class LoanFilter(django_filters.FilterSet):
    loanid=django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model=Loan
        fields=['loanid','license','customer','itemtype','license']
