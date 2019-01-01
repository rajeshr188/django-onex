from django.contrib import admin
from django import forms
from .models import Invoice, InvoiceItem, Payment
from contact.models import Supplier
from import_export import fields,resources
from import_export.admin import ImportExportModelAdmin,ImportExportActionModelAdmin
from import_export.widgets import ForeignKeyWidget

class InvoiceAdminForm(forms.ModelForm):

    class Meta:
        model = Invoice
        fields = '__all__'

class InvoiceResource(resources.ModelResource):
    supplier = fields.Field(column_name = 'supplier',attribute = 'supplier',
                                widget=ForeignKeyWidget(Supplier,'pk'))
    class Meta:
        model = Invoice
        fields=('id','supplier','created','rate','balancetype','paymenttype','balance','status',)

class InvoiceAdmin(ImportExportActionModelAdmin):
    form = InvoiceAdminForm
    resource_class = InvoiceResource
    list_display = ['id','slug', 'created', 'last_updated', 'rate', 'balancetype', 'paymenttype', 'balance', 'status']

admin.site.register(Invoice, InvoiceAdmin)


class InvoiceItemAdminForm(forms.ModelForm):

    class Meta:
        model = InvoiceItem
        fields = '__all__'

class InvoiceItemAdmin(admin.ModelAdmin):
    form = InvoiceItemAdminForm
    list_display = ['weight', 'touch', 'total', 'is_return', 'quantity']

admin.site.register(InvoiceItem, InvoiceItemAdmin)

class PaymentAdminForm(forms.ModelForm):

    class Meta:
        model = Payment
        fields = '__all__'

class PaymentResourse(resources.ModelResource):
    invoice = fields.Field(column_name = 'invoice',attribute = 'invoice',
                                widget= ForeignKeyWidget(Invoice,'pk'))
    supplier = fields.Field(column_name = 'supplier',attribute = 'supplier',
                                widget=ForeignKeyWidget(Supplier,'pk')
                    )
    class Meta:
        model = Payment

class PaymentAdmin(ImportExportActionModelAdmin):
    form = PaymentAdminForm
    resource_class = PaymentResourse
    list_display = ['id','slug', 'created', 'last_updated', 'type', 'total', 'description']


admin.site.register(Payment, PaymentAdmin)
