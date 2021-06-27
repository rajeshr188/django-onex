from django.contrib.auth.models import User
import django_filters
from .models import ApprovalLine

class ApprovalLineFilter(django_filters.FilterSet):
    class Meta:
        model = ApprovalLine
        fields = ['approval__contact','approval__bill']
