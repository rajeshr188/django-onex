import django_filters
from django.contrib.auth.models import User

from .models import ApprovalLine


class ApprovalLineFilter(django_filters.FilterSet):
    class Meta:
        model = ApprovalLine
        fields = [
            "approval__contact",
        ]
