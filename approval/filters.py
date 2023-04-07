import django_filters

from .models import ApprovalLine
from contact.forms import CustomerWidget

class ApprovalLineFilter(django_filters.FilterSet):
    class Meta:
        model = ApprovalLine
        fields = [
            "approval__contact",
        ]
        widgets = {
            "approval__contact": CustomerWidget,
        }

