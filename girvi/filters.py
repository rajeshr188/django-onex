import django_filters

from contact.forms import CustomerWidget
from contact.models import Customer
from girvi.forms import LoansWidget

from .models import Adjustment, Loan, LoanStatement, Release


class LoanFilter(django_filters.FilterSet):
    loanid = django_filters.CharFilter(lookup_expr="icontains")
    itemdesc = django_filters.CharFilter(lookup_expr="icontains")
    customer = django_filters.ModelChoiceFilter(
        queryset=Customer.objects.filter(type="Re"), widget=CustomerWidget
    )
    Status = django_filters.BooleanFilter(field_name="release", method="filter_status")
    from_date = django_filters.DateFilter("created", lookup_expr="gte")
    till_date = django_filters.DateFilter("created", lookup_expr="lte")
    notice = django_filters.CharFilter(field_name="notifications__notice_type", lookup_expr="icontains")

    def filter_status(self, queryset, name, value):
        return queryset.filter(release__isnull=value)

    class Meta:
        model = Loan
        fields = [
            "loanid",
            "series",
            "customer",
            "itemtype",
            "itemweight",
            "itemdesc",
            "loanamount",
        ]


class LoanStatementFilter(django_filters.FilterSet):
    loan = django_filters.ModelChoiceFilter(
        widget=LoansWidget, queryset=Loan.objects.filter(series__is_active=True)
    )

    class Meta:
        model = LoanStatement
        fields = ["loan"]


class AdjustmentFilter(django_filters.FilterSet):
    class Meta:
        model = Adjustment
        fields = ["loan"]


class ReleaseFilter(django_filters.FilterSet):
    loan = django_filters.ModelChoiceFilter(
        widget=LoansWidget, queryset=Loan.released.all()
    )

    class Meta:
        model = Release
        fields = ["releaseid", "loan"]
