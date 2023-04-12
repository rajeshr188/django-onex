from decimal import Decimal

import django_filters
from django.db.models import Q
from django_select2.forms import Select2Widget

from contact.forms import CustomerWidget
from contact.models import Customer
from girvi.forms import LoansWidget

from .models import Adjustment, Loan, LoanStatement, Release


class LoanFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="Search")
    # loanid = django_filters.CharFilter(lookup_expr="icontains")
    # itemdesc = django_filters.CharFilter(lookup_expr="icontains")
    customer = django_filters.ModelChoiceFilter(
        queryset=Customer.objects.all(),
        widget=CustomerWidget(empty_label="Customer"),
        # queryset = Customer.objects.all(),
        # widget = Select2Widget
    )
    posted = django_filters.BooleanFilter(field_name="posted")
    status = django_filters.BooleanFilter(field_name="release", method="filter_status")
    from_date = django_filters.DateFilter("created", lookup_expr="gte")
    till_date = django_filters.DateFilter("created", lookup_expr="lte")
    # notice = django_filters.CharFilter(
    #     field_name="notifications__notice_type", lookup_expr="icontains"
    # )
    # create a filter for loan_type field with choices
    loan_type = django_filters.ChoiceFilter(choices = Loan.LoanType.choices, empty_label="Select Loan Type")
    sunk = django_filters.BooleanFilter(method="sunken", label="sunken")

    def filter_status(self, queryset, name, value):
        return queryset.filter(release__isnull=value)

    class Meta:
        model = Loan
        fields = [
            "query",
            "series",
            "customer",
            "itemtype",
        ]

    def universal_search(self, queryset, name, value):
        # if value.replace(".", "", 1).isdigit():
        #     value = Decimal(value)
        #     return Customer.objects.filter(
        #         Q(price=value) | Q(cost=value)
        #     )

        return Loan.objects.filter(
            Q(id__icontains=value)
            | Q(lid__icontains=value)
            | Q(loanid__icontains=value)
            | Q(itemdesc__icontains=value)
            | Q(itemweight__icontains=value)
            | Q(loanamount__icontains=value)
        )

    def sunken(self, queryset, name, value):
        return queryset.filter(is_overdue=value)


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
