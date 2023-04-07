import django_filters

from contact.forms import CustomerWidget

from .models import ApprovalLine


class ApprovalLineFilter(django_filters.FilterSet):
    class Meta:
        model = ApprovalLine
        fields = [
            "approval__contact",
        ]
        widgets = {
            "approval__contact": CustomerWidget,
        }
