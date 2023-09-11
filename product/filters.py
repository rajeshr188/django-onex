import django_filters
from django_select2.forms import Select2MultipleWidget, Select2Widget

from .models import (
    Attribute,
    AttributeValue,
    Category,
    Product,
    ProductType,
    ProductVariant,
    Stock,
    StockLot,
    StockTransaction,
)


class StockFilter(django_filters.FilterSet):
    variant = django_filters.ModelChoiceFilter(
        queryset=ProductVariant.objects.all(), widget=Select2Widget
    )

    class Meta:
        model = StockLot
        fields = ["variant"]


class StockLotFilter(django_filters.FilterSet):
    variant = django_filters.ModelChoiceFilter(
        queryset=ProductVariant.objects.all(), widget=Select2Widget
    )

    class Meta:
        model = StockLot
        fields = ["variant", "stock", "barcode", "huid"]


class StockTransactionFilter(django_filters.FilterSet):
    class Meta:
        model = StockTransaction
        fields = "__all__"


class ProductFilter(django_filters.FilterSet):
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(), widget=Select2Widget
    )
    product_type = django_filters.ModelChoiceFilter(
        queryset=ProductType.objects.all(), widget=Select2Widget
    )

    class Meta:
        model = Product
        fields = ["category", "product_type"]


class ProductVariantFilter(django_filters.FilterSet):
    product = django_filters.ModelChoiceFilter(
        queryset=Product.objects.all(), widget=Select2Widget
    )
    attributes = django_filters.ModelMultipleChoiceFilter(
        queryset=AttributeValue.objects.all(),
        widget=Select2MultipleWidget,
    )

    class Meta:
        model = ProductVariant
        fields = ["product"]
