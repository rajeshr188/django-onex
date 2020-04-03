from .models import Stree
import django_filters
from django_select2.forms import Select2Widget

class StreeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='iexact')
    class Meta:
        model = Stree
        fields = ['name','barcode']
