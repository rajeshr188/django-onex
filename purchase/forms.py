from django import forms
from .models import Invoice, InvoiceItem, Payment
from django_select2.forms import Select2Widget,ModelSelect2Widget
from contact.models import Supplier
from product.models import ProductVariant
from django.forms.models import inlineformset_factory


class InvoiceForm(forms.ModelForm):
    supplier=forms.ModelChoiceField(queryset=Supplier.objects.all(),widget=Select2Widget)
    class Meta:
        model = Invoice
        fields = ['created','rate', 'balancetype', 'paymenttype', 'balance', 'status', 'supplier']


class InvoiceItemForm(forms.ModelForm):
    product=forms.ModelChoiceField(queryset=ProductVariant.objects.all(),widget=Select2Widget)


    class Meta:
        model = InvoiceItem
        fields = ['weight', 'touch', 'total', 'is_return', 'quantity', 'product', 'invoice','makingcharge']

InvoiceItemFormSet=inlineformset_factory(Invoice,InvoiceItem,
    fields=('is_return','product','quantity','weight', 'touch', 'makingcharge','total', 'invoice'),extra=1,can_delete=True)

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['type', 'total', 'description', 'supplier']
