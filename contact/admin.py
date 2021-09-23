from django.contrib import admin
from django import forms
from import_export import fields,resources
from import_export.admin import ImportExportModelAdmin,ImportExportActionModelAdmin
from import_export.widgets import ForeignKeyWidget
from .models import Customer
from utils.tenant_admin import admin_site

class CustomerResource(resources.ModelResource):

    class Meta:
        model=Customer
        use_bulk = True

class CustomerAdminForm(forms.ModelForm):

    class Meta:
        model = Customer
        fields = '__all__'

class CustomerAdmin(ImportExportActionModelAdmin):
    form = CustomerAdminForm
    resource_class=CustomerResource
    list_display = ['name', 'id', 'created', 'updated', 'phonenumber', 'Address','area', 'type', 'relatedas', 'relatedto']
    # readonly_fields = ['name', 'id', 'created', 'updated', 'phonenumber', 'Address', 'area','type', 'relatedas', 'relatedto']

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request) -> bool:
        return True

admin_site.register(Customer, CustomerAdmin)
