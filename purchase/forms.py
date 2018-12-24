from django import forms
from .models import Invoice, InvoiceItem, Payment,PaymentLine
from django_select2.forms import Select2Widget,ModelSelect2Widget
from contact.models import Supplier
from product.models import ProductVariant
from django.forms.models import inlineformset_factory
from django.db.models import Q

class InvoiceForm(forms.ModelForm):
    supplier=forms.ModelChoiceField(queryset=Supplier.objects.all(),widget=Select2Widget)
    class Meta:
        model = Invoice
        fields = ['created','rate', 'balancetype', 'paymenttype', 'balance', 'supplier']


class InvoiceItemForm(forms.ModelForm):
    product=forms.ModelChoiceField(queryset=ProductVariant.objects.all(),widget=Select2Widget)


    class Meta:
        model = InvoiceItem
        fields = ['weight', 'touch', 'total', 'is_return', 'quantity', 'product', 'invoice','makingcharge']

InvoiceItemFormSet=inlineformset_factory(Invoice,InvoiceItem,
    fields=('is_return','product','quantity','weight', 'touch', 'makingcharge','total', 'invoice'),extra=1,can_delete=True)

class PaymentForm(forms.ModelForm):
    supplier=forms.ModelChoiceField(queryset=Supplier.objects.all(),widget=Select2Widget)
    class Meta:
        model = Payment
        fields = ['supplier','type', 'weight','touch','nettwt','rate','total', 'description' ]

class PaymentLineForm(forms.ModelForm):

    invoice=forms.ModelChoiceField(
                                    queryset=Invoice.objects.filter(Q(status="Unpaid")|Q(status="PartiallyPaid")),
                                    widget=Select2Widget,
    )
    class Meta:
        model=PaymentLine
        fields=['invoice','amount']

PaymentLineFormSet=inlineformset_factory(Payment,PaymentLine,
    fields=('invoice','amount','payment'),extra=1,can_delete=True,form=PaymentLineForm)
