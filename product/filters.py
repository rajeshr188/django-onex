from .models import (Category,ProductType,Product,
                        Stock,StockBalance,StockTransaction,ProductVariant,
                        Attribute,AttributeValue)
import django_filters
from django_select2.forms import Select2Widget,Select2MultipleWidget

class StockFilter(django_filters.FilterSet):

    stock__variant = django_filters.ModelChoiceFilter(
                    queryset = ProductVariant.objects.all(),
                    widget = Select2Widget
    )

    class Meta:
        model = StockBalance
        fields = ['stock__variant','stock__barcode','stock__huid']

class StockTransactionFilter(django_filters.FilterSet):
    class Meta:
        model = StockTransaction
        fields = '__all__'

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
    attributes = django_filters.ModelMultipleChoiceFilter(
                    queryset = AttributeValue.objects.all(),
                    widget = Select2MultipleWidget,
    )
   
    class Meta:
        model = ProductVariant
        fields = ['product','product_code']
