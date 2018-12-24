from django import forms
from .models import Invoice, InvoiceItem, Receipt,ReceiptLine
from django_select2.forms import Select2Widget,ModelSelect2Widget,ModelSelect2MultipleWidget
from contact.models import Customer
from product.models import ProductVariant
from django.forms.models import inlineformset_factory
from django.db.models import Q

class InvoiceForm(forms.ModelForm):
    customer=forms.ModelChoiceField(queryset=Customer.objects.all(),widget=Select2Widget)
    class Meta:
        model = Invoice
        fields = ['created','rate', 'balancetype', 'paymenttype', 'balance', 'customer']


class InvoiceItemForm(forms.ModelForm):
    product=forms.ModelChoiceField(queryset=ProductVariant.objects.all(),widget=Select2Widget)


    class Meta:
        model = InvoiceItem
        fields = ['weight', 'touch', 'total', 'is_return', 'quantity', 'product', 'invoice','makingcharge']

InvoiceItemFormSet=inlineformset_factory(Invoice,InvoiceItem,
    fields=('is_return','product','quantity','weight', 'touch', 'makingcharge','total', 'invoice'),extra=1,can_delete=True)

class ReceiptForm(forms.ModelForm):
    customer=forms.ModelChoiceField(queryset=Customer.objects.all(),widget=Select2Widget)

    class Meta:
        model = Receipt
        fields = ['customer','type', 'weight','touch','nettwt','rate','total', 'description']

class ReceiptLineForm(forms.ModelForm):
    # invoice=forms.ModelChoiceField(
    #                                 queryset=Invoice.objects.all(),
    #                                 widget=ModelSelect2Widget(
    #                                 model=Invoice,search_fields=['name__icontains'],dependent_fields={'customer':'customer'}),
    # )
    invoice=forms.ModelChoiceField(
                                    queryset=Invoice.objects.filter(Q(status="Unpaid")|Q(status="PartiallyPaid")),
                                    widget=Select2Widget,
    )
    class Meta:
        model=ReceiptLine
        fields=['invoice','amount']

ReceiptLineFormSet=inlineformset_factory(Receipt,ReceiptLine,
    fields=('invoice','amount','receipt'),extra=1,can_delete=True,form=ReceiptLineForm)
