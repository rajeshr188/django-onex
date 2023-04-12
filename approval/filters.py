import django_filters

from contact.forms import CustomerWidget
from contact.models import Customer
from product.models import StockLot
from django_select2.forms import ModelSelect2Widget
from .models import ApprovalLine, Approval

class ApprovalFilter(django_filters.FilterSet):
    contact = django_filters.ModelChoiceFilter(
        queryset=Customer.objects.all(),
        widget=CustomerWidget(empty_label="Customer"),
    )
    class Meta:
        model = Approval
        fields = [
            "contact",
            "status",
            "is_billed",
            "posted"
        ]

class ApprovalLineFilter(django_filters.FilterSet):
    approval__contact = django_filters.ModelChoiceFilter(
        queryset=Customer.objects.all(),
        widget=CustomerWidget(empty_label="Customer"),
    )
    product = django_filters.ModelChoiceFilter(
        queryset=StockLot.objects.all(),
        widget=ModelSelect2Widget(empty_label="stock",search_fields=['variant__name__icontains']),
    )
    class Meta:
        model = ApprovalLine
        fields = [
            "approval__contact",
        ]