from django.contrib import admin
from django import forms
from .models import Invoice, InvoiceItem, Receipt
from contact.models import Customer
from import_export import fields,resources
from import_export.admin import ImportExportModelAdmin,ImportExportActionModelAdmin
from import_export.widgets import ForeignKeyWidget

class InvoiceAdminForm(forms.ModelForm):

    class Meta:
        model = Invoice
        fields = '__all__'

class InvoiceResource(resources.ModelResource):
    customer = fields.Field(column_name='customer',attribute='customer',
                            widget=ForeignKeyWidget(Customer,'pk'))
    class Meta:
        model = Invoice
        fields = ('id','customer','created','rate','balancetype','paymenttype','balance','status',)

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
                            widget=ForeignKeyWidget(Customer,'pk'))
    invoice = fields.Field(column_name = 'invoice',attribute = 'invoice',
                                widget= ForeignKeyWidget(Invoice,'pk'))

    class Meta:
        model = Receipt

class ReceiptAdmin(ImportExportActionModelAdmin):
    form = ReceiptAdminForm
    resource_class = ReceiptResource
    list_display = ['id','created', 'last_updated', 'type', 'total', 'description']


admin.site.register(Receipt, ReceiptAdmin)
