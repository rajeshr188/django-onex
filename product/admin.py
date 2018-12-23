from django.contrib import admin

# Register your models here.
from django import forms
from .models import Category, ProductType, Product, ProductVariant, Attribute, AttributeValue, ProductImage, VariantImage

class CategoryAdminForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = '__all__'


class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ['name', 'description']
    # readonly_fields = ['name', 'description']

admin.site.register(Category, CategoryAdmin)


class ProductTypeAdminForm(forms.ModelForm):

    class Meta:
        model = ProductType
        fields = '__all__'


class ProductTypeAdmin(admin.ModelAdmin):
    form = ProductTypeAdminForm
    list_display = ['name', 'has_variants']
    # readonly_fields = ['name', 'has_variants']

admin.site.register(ProductType, ProductTypeAdmin)


class ProductAdminForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = '__all__'


class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ['name', 'description']
    # readonly_fields = ['name', 'description']

admin.site.register(Product, ProductAdmin)


class ProductVariantAdminForm(forms.ModelForm):

    class Meta:
        model = ProductVariant
        fields = '__all__'


class ProductVariantAdmin(admin.ModelAdmin):
    form = ProductVariantAdminForm
    list_display = ['sku', 'name', 'track_inventory', 'quantity', 'cost_price', 'weight']
    # readonly_fields = ['sku', 'name', 'track_inventory', 'quantity', 'cost_price', 'weight']

admin.site.register(ProductVariant, ProductVariantAdmin)


class AttributeAdminForm(forms.ModelForm):

    class Meta:
        model = Attribute
        fields = '__all__'


class AttributeAdmin(admin.ModelAdmin):
    form = AttributeAdminForm
    list_display = ['slug', 'name']
    readonly_fields = ['slug', 'name']

admin.site.register(Attribute, AttributeAdmin)


class AttributeValueAdminForm(forms.ModelForm):

    class Meta:
        model = AttributeValue
        fields = '__all__'


class AttributeValueAdmin(admin.ModelAdmin):
    form = AttributeValueAdminForm
    list_display = ['name', 'value', 'slug']
    readonly_fields = ['name', 'value', 'slug']

admin.site.register(AttributeValue, AttributeValueAdmin)


class ProductImageAdminForm(forms.ModelForm):

    class Meta:
        model = ProductImage
        fields = '__all__'


class ProductImageAdmin(admin.ModelAdmin):
    form = ProductImageAdminForm
    # list_display = ['ppoi', 'alt']
    # readonly_fields = ['ppoi', 'alt']

admin.site.register(ProductImage, ProductImageAdmin)


class VariantImageAdminForm(forms.ModelForm):

    class Meta:
        model = VariantImage
        fields = '__all__'


class VariantImageAdmin(admin.ModelAdmin):
    form = VariantImageAdminForm


admin.site.register(VariantImage, VariantImageAdmin)
