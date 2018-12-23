from django.contrib import admin
from django import forms
from .models import Invoice, InvoiceItem, Receipt

class InvoiceAdminForm(forms.ModelForm):

    class Meta:
        model = Invoice
        fields = '__all__'


class InvoiceAdmin(admin.ModelAdmin):
    form = InvoiceAdminForm
    list_display = ['slug', 'created', 'last_updated', 'rate', 'balancetype', 'paymenttype', 'balance', 'status']
    readonly_fields = ['slug', 'created', 'last_updated', 'rate', 'balancetype', 'paymenttype', 'balance', 'status']

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


class ReceiptAdmin(admin.ModelAdmin):
    form = ReceiptAdminForm
    list_display = ['slug', 'created', 'last_updated', 'type', 'total', 'description']
    readonly_fields = ['slug', 'created', 'last_updated', 'type', 'total', 'description']

admin.site.register(Receipt, ReceiptAdmin)


