from django import forms
from mptt.forms import TreeNodeChoiceField
from django.utils.translation import pgettext_lazy
from .models import Category, ProductType, Product, ProductVariant, Attribute, AttributeValue, ProductImage, VariantImage,Stock,StockTransaction
from django.shortcuts import get_object_or_404
from django.utils.encoding import smart_text
from .attributes import get_name_from_attributes,get_product_attributes_data,generate_name_from_values
from django.forms.widgets import CheckboxSelectMultiple

class ModelChoiceOrCreationField(forms.ModelChoiceField):
    """ModelChoiceField with the ability to create new choices.

    This field allows to select values from a queryset, but it also accepts
    new values that can be used to create new model choices.
    """

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            key = self.to_field_name or 'pk'
            obj = self.queryset.get(**{key: value})
        except (ValueError, TypeError, self.queryset.model.DoesNotExist):
            return value
        else:
            return obj
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name',  'description', 'parent']


class ProductTypeForm(forms.ModelForm):
    product_attributes=forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple,queryset=Attribute.objects.all(),required=False)
    variant_attributes=forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple,queryset=Attribute.objects.all(),required=False)
    class Meta:
        model = ProductType
        exclude = []
        labels = {
            'name': pgettext_lazy(
                'Item name',
                'Name'),
            'has_variants': pgettext_lazy(
                'Enable variants',
                'Enable variants'),
            'variant_attributes': pgettext_lazy(
                'Product type attributes',
                'Attributes specific to each variant'),
            'product_attributes': pgettext_lazy(
                'Product type attributes',
                'Attributes common to all variants'),
            }
    def clean(self):
        data = super().clean()
        has_variants = self.cleaned_data['has_variants']
        product_attr = set(self.cleaned_data['product_attributes'])
        variant_attr = set(self.cleaned_data['variant_attributes'])
        if not has_variants and variant_attr:
            msg = pgettext_lazy(
                'Product type form error',
                'Product variants are disabled.')
            self.add_error('variant_attributes', msg)
        if product_attr & variant_attr:
            msg = pgettext_lazy(
                'Product type form error',
                'A single attribute can\'t belong to both a product '
                'and its variant.')
            self.add_error('variant_attributes', msg)

        if not self.instance.pk:
            return data

        # self.check_if_variants_changed(has_variants)
        # self.update_variants_names(saved_attributes=variant_attr)
        return data



class AttributesMixin:
    """Form mixin that dynamically adds attribute fields."""

    available_attributes = Attribute.objects.none()

    # Name of a field in self.instance that hold attributes HStore
    model_attributes_field = None

    def __init__(self, *args, **kwargs):
        if not self.model_attributes_field:
            raise Exception(
                'model_attributes_field must be set in subclasses of '
                'AttributesMixin.')

    def prepare_fields_for_attributes(self):
        initial_attrs = getattr(self.instance, self.model_attributes_field)
        for attribute in self.available_attributes:
            field_defaults = {
                'label': attribute.name, 'required': False,
                'initial': initial_attrs.get(str(attribute.pk))}
            if attribute.has_values():
                field = ModelChoiceOrCreationField(
                    queryset=attribute.values.all(), **field_defaults)
            else:
                field = forms.CharField(**field_defaults)
            self.fields[attribute.get_formfield_name()] = field

    def iter_attribute_fields(self):
        for attr in self.available_attributes:
            yield self[attr.get_formfield_name()]

    def get_saved_attributes(self):
        attributes = {}
        for attr in self.available_attributes:
            value = self.cleaned_data.pop(attr.get_formfield_name())
            if value:
                # if the passed attribute value is a string,
                # create the attribute value.
                if not isinstance(value, AttributeValue):
                    value = AttributeValue(
                        attribute_id=attr.pk, name=value, slug=slugify(value))
                    value.save()
                attributes[smart_text(attr.pk)] = smart_text(value.pk)
        return attributes
class ProductForm(forms.ModelForm, AttributesMixin):
    category = TreeNodeChoiceField(
        queryset=Category.objects.all(),label=pgettext_lazy('Category', 'Category'))
    model_attributes_field = 'attributes'
    class Meta:
        model = Product
        exclude = ['attributes','product_type','name']

    def __init__(self,*args,**kwargs):
        super(ProductForm,self).__init__(*args,**kwargs)
        product_type = self.instance.product_type
        self.available_attributes = (
            product_type.product_attributes.prefetch_related('values').all())
        self.prepare_fields_for_attributes()
        # self.fields['attributes']=forms.ModelMultipleChoiceField(queryset=Attribute.objects.all())
    def save(self, commit=True):
        attributes = self.get_saved_attributes()
        self.instance.attributes = attributes
        attrs = get_product_attributes_data(self.instance)
        self.instance.name = self.instance.product_type.name + ' /'+generate_name_from_values(attrs)
        instance = super().save()
        return instance
class ProductVariantForm(forms.ModelForm, AttributesMixin):
    model_attributes_field = 'attributes'

    class Meta:
        model = ProductVariant
        fields = [
            'sku','weight',
            'quantity', 'cost_price', 'selling_price','track_inventory']
        labels = {
            'sku': pgettext_lazy('SKU', 'SKU'),
            'quantity': pgettext_lazy('Integer number', 'Number in stock'),
            'cost_price': pgettext_lazy('Currency amount', 'Cost price'),
            'track_inventory': pgettext_lazy(
                'Track inventory field', 'Track inventory')}
        help_texts = {
            'track_inventory': pgettext_lazy(
                'product variant handle stock field help text',
                'Automatically track this product\'s inventory')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.product.pk:
            self.available_attributes = (
                self.instance.product.product_type.variant_attributes.all()
                    .prefetch_related('values'))
            self.prepare_fields_for_attributes()


    def save(self, commit=True):
        attributes = self.get_saved_attributes()
        self.instance.attributes = attributes
        attrs = self.instance.product.product_type.variant_attributes.all()
        self.instance.name = get_name_from_attributes(self.instance, attrs)
        return super().save(commit=commit)

class AttributeForm(forms.ModelForm):
    class Meta:
        model = Attribute
        fields = [ 'name']


class AttributeValueForm(forms.ModelForm):
    class Meta:
        model = AttributeValue
        fields = ['name', 'value',  'attribute']


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = [ 'alt']


class VariantImageForm(forms.ModelForm):
    class Meta:
        model = VariantImage
        fields = '__all__'

class StockForm(forms.ModelForm):
    class Meta:
        model=Stock
        fields='__all__'

class StockTransactionForm(forms.ModelForm):
    class Meta:
        model=StockTransaction
        exclude=['created','updated']
