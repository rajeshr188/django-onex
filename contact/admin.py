from django.contrib import admin
from django import forms
from import_export import fields,resources
from import_export.admin import ImportExportModelAdmin,ImportExportActionModelAdmin
from import_export.widgets import ForeignKeyWidget
from .models import Customer

class CustomerResource(resources.ModelResource):

    class Meta:
        model=Customer

class CustomerAdminForm(forms.ModelForm):

    class Meta:
        model = Customer
        fields = '__all__'

class CustomerAdmin(ImportExportActionModelAdmin):
    form = CustomerAdminForm
    resource_class=CustomerResource
    search_fields = ['name','relatedto', 'Address', 'phonenumber']
    list_display = ['name', 'id', 'created', 'updated', 'phonenumber', 'Address','area', 'type', 'relatedas', 'relatedto']
    readonly_fields = ['name', 'id', 'created', 'updated', 'phonenumber', 'Address', 'area','type', 'relatedas', 'relatedto']

admin.site.register(Customer, CustomerAdmin)


