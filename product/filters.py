from .models import Stree,Category,ProductType,Product,ProductVariant,Attribute
import django_filters
from django_select2.forms import Select2Widget

class StreeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='iexact')
    class Meta:
        model = Stree
        fields = ['name','barcode']

class ProductFilter(django_filters.FilterSet):
    category = django_filters.ModelChoiceFilter(
                        queryset = Category.objects.all(),
                        widget = Select2Widget
    )
    product_type = django_filters.ModelChoiceFilter(
                        queryset = ProductType.objects.all(),
                        widget = Select2Widget
    )
    class Meta:
        model = Product
        fields = ['category','product_type']

class ProductVariantFilter(django_filters.FilterSet):
    product = django_filters.ModelChoiceFilter(
                    queryset = Product.objects.all(),
                    widget = Select2Widget
    )
    # atttributes = django_filters.ModelChoiceFilter(
    #                 queryset = Attribute.objects.all(),
    #                 widget = Select2Widget
    # )
    class Meta:
        model = ProductVariant
        fields = ['product',]
