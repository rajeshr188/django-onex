from django.contrib import admin
from django import forms
from .models import Invoice, InvoiceItem, Payment

class InvoiceAdminForm(forms.ModelForm):

    class Meta:
        model = Invoice
        fields = '__all__'

class InvoiceAdmin(admin.ModelAdmin):
    form = InvoiceAdminForm
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

class PaymentAdmin(admin.ModelAdmin):
    form = PaymentAdminForm
    list_display = ['id','slug', 'created', 'last_updated', 'type', 'total', 'description']


admin.site.register(Payment, PaymentAdmin)
