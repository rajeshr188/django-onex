from .models import Customer
import django_filters

class CustomerFilter(django_filters.FilterSet):
    name=django_filters.CharFilter(lookup_expr='icontains')
    relatedto=django_filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model=Customer
        fields=['id','name','relatedto','phonenumber','type','active']
