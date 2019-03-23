from django.contrib import admin
from django import forms
from .models import Invoice, InvoiceItem, Receipt
from contact.models import Customer
from import_export import fields,resources
from import_export.admin import ImportExportModelAdmin,ImportExportActionModelAdmin
from import_export.widgets import ForeignKeyWidget,DecimalWidget

from import_export import widgets
import decimal
class CustomDecimalWidget(widgets.DecimalWidget):
    """
    Widget for converting decimal fields.
    """

    def clean(self, value,row=None):
        if self.is_empty(value):
            return None
        return decimal.Decimal(str(value))

class customerWidget(widgets.ForeignKeyWidget):

    # def clean(self, value):
    #     if value:
    #         return self.model.objects.get_or_create(
    #             name=val,type='Wh',
    #         )
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
        fields = ('id','customer','created','rate','balancetype','paymenttype','balance','status',)
        skip_unchanged = True
        report_skipped = False

class InvoiceAdmin(ImportExportActionModelAdmin):
    form = InvoiceAdminForm
    resource_class = InvoiceResource
    list_display = ['id', 'created', 'last_updated', 'rate', 'balancetype', 'paymenttype', 'balance', 'status']

admin.site.register(Invoice, InvoiceAdmin)


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
    # invoice = fields.Field(column_name = 'invoice',attribute = 'invoice',
    #                             widget= ForeignKeyWidget(Invoice,'pk'))
    total = fields.Field(column_name = 'total',attribute='total',
                            widget = CustomDecimalWidget())

    class Meta:
        model = Receipt
        fields=('id','customer','created','last_updated','type','total','description','status')
        skip_unchanged = True
        report_skipped = False

class ReceiptAdmin(ImportExportActionModelAdmin):
    form = ReceiptAdminForm
    resource_class = ReceiptResource
    list_display = ['id','customer','created', 'last_updated', 'type', 'total', 'description','status']


admin.site.register(Receipt, ReceiptAdmin)
