from django.contrib import admin
from django import forms
from .models import Invoice, InvoiceItem, Receipt
from contact.models import Customer
from import_export import fields,resources
from import_export.admin import ImportExportModelAdmin,ImportExportActionModelAdmin
from import_export.widgets import ForeignKeyWidget,DecimalWidget
import decimal
from utils.tenant_admin import admin_site
class CustomDecimalWidget(DecimalWidget):
    """
    Widget for converting decimal fields.
    """
    def clean(self, value,row=None):
        if self.is_empty(value):
            return None
        return decimal.Decimal(str(value))

class customerWidget(ForeignKeyWidget):

    def clean(self, value, row=None, *args, **kwargs):
        return self.model.objects.get_or_create(name = value,type='Wh')[0]

class InvoiceAdminForm(forms.ModelForm):

    class Meta:
        model = Invoice
        fields = '__all__'

class InvoiceResource(resources.ModelResource):
    # customer = fields.Field(column_name='customer',attribute='customer',
    #                         widget=ForeignKeyWidget(Customer,'name'))
    customer = fields.Field(column_name='customer',attribute='customer',
                            widget=customerWidget(Customer,'name'))
    class Meta:
        model = Invoice
        fields = ('id','customer','created','rate','balancetype','balance','status',)
        skip_unchanged = True
        report_skipped = False

class InvoiceAdmin(ImportExportActionModelAdmin):
    form = InvoiceAdminForm
    resource_class = InvoiceResource
    list_display = ['id', 'created', 'updated', 'rate', 'balancetype', 'balance', 'status']

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request) -> bool:
        return True

admin_site.register(Invoice, InvoiceAdmin)


class InvoiceItemAdminForm(forms.ModelForm):

    class Meta:
        model = InvoiceItem
        fields = '__all__'


class InvoiceItemAdmin(admin.ModelAdmin):
    form = InvoiceItemAdminForm
    list_display = ['weight', 'touch', 'total', 'is_return', 'quantity']
    readonly_fields = ['weight', 'touch', 'total', 'is_return', 'quantity']

admin.site.register(InvoiceItem, InvoiceItemAdmin)


class ReceiptAdminForm(forms.ModelForm):

    class Meta:
        model = Receipt
        fields = '__all__'

class ReceiptResource(resources.ModelResource):
    customer=fields.Field(column_name='customer',
                            attribute='customer',
                            widget=ForeignKeyWidget(Customer,'name'))
    total = fields.Field(column_name = 'total',attribute='total',
                            widget = CustomDecimalWidget())
    class Meta:
        model = Receipt
        fields=('id','customer','created','updated','type','total','description','status')
        skip_unchanged = True
        report_skipped = False

class ReceiptAdmin(ImportExportActionModelAdmin):
    form = ReceiptAdminForm
    resource_class = ReceiptResource
    list_display = ['id','customer','created', 'updated', 'type', 'total', 'description','status']

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request) -> bool:
        return True

admin_site.register(Receipt, ReceiptAdmin)
