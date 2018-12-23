from django.contrib import admin
from django import forms
from import_export import fields,resources
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from .models import Customer, Supplier

class CustomerResource(resources.ModelResource):

    class Meta:
        model=Customer

class CustomerAdminForm(forms.ModelForm):

    class Meta:
        model = Customer
        fields = '__all__'

class CustomerAdmin(ImportExportModelAdmin):
    form = CustomerAdminForm
    resource_class=CustomerResource
    list_display = ['name', 'id', 'created', 'last_updated', 'phonenumber', 'Address','area', 'type', 'relatedas', 'relatedto']
    readonly_fields = ['name', 'id', 'created', 'last_updated', 'phonenumber', 'Address', 'area','type', 'relatedas', 'relatedto']

admin.site.register(Customer, CustomerAdmin)


class SupplierAdminForm(forms.ModelForm):

    class Meta:
        model = Supplier
        fields = '__all__'


class SupplierAdmin(admin.ModelAdmin):
    form = SupplierAdminForm
    list_display = ['name', 'slug', 'created', 'last_updated', 'organisation', 'phonenumber', 'initial']
    readonly_fields = ['name', 'slug', 'created', 'last_updated', 'organisation', 'phonenumber', 'initial']

admin.site.register(Supplier, SupplierAdmin)
