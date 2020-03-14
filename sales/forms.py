from django import forms
import datetime
from tempus_dominus.widgets import DatePicker, TimePicker, DateTimePicker
from .models import Invoice, InvoiceItem, Receipt,ReceiptLine
from django_select2.forms import Select2Widget,ModelSelect2Widget,ModelSelect2MultipleWidget
from contact.models import Customer
from product.models import ProductVariant
from django.forms.models import inlineformset_factory
from django.db.models import Q

class RandomSalesForm(forms.Form):
    month = forms.IntegerField(required = True)

class InvoiceForm(forms.ModelForm):
    created = forms.DateTimeField(
        widget=DateTimePicker(
            options={
                'defaultDate': (datetime.datetime.now()).strftime("%m/%d/%Y, %H:%M:%S"),
                'minDate': '2009-01-20',# 'minDate': (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),  # Tomorrow
                'useCurrent': True,
                'collapse': False,
            },
            attrs={
               'append': 'fa fa-calendar',
               'input_toggle': False,
               'icon_toggle': True,
            }
        ),
    )
    customer=forms.ModelChoiceField(queryset=Customer.objects.exclude(type='Re'),widget=Select2Widget)
    class Meta:
        model = Invoice
        fields = ['created','rate', 'balancetype', 'paymenttype', 'balance', 'customer','status']

class InvoiceItemForm(forms.ModelForm):
    product=forms.ModelChoiceField(queryset=ProductVariant.objects.all(),widget=Select2Widget)

    class Meta:
        model = InvoiceItem
        fields = ['weight', 'touch', 'total', 'is_return', 'quantity', 'product', 'invoice','makingcharge']

InvoiceItemFormSet=inlineformset_factory(Invoice,InvoiceItem,
    fields=('is_return','product','quantity','weight', 'touch', 'makingcharge','total', 'invoice'),extra=1,can_delete=True)

class ReceiptForm(forms.ModelForm):
    customer=forms.ModelChoiceField(queryset=Customer.objects.filter(type='Wh'),widget=Select2Widget)
    created = forms.DateTimeField(
        widget=DateTimePicker(
            options={
                'defaultDate': (datetime.date.today()).strftime('%Y-%m-%d'),
                'minDate': '2013-02-07',#(datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),  # Tomorrow
                'useCurrent': True,
                'collapse': False,
            },
            attrs={
               'append': 'fa fa-calendar',
               'input_toggle': False,
               'icon_toggle': True,
            }
        ),
    )
    class Meta:
        model = Receipt
        fields = ['created','customer','type', 'weight','touch','nettwt','rate','total', 'description','status']

class ReceiptLineForm(forms.ModelForm):
    # invoice=forms.ModelChoiceField(
    #                                 queryset=Invoice.objects.all(),
    #                                 widget=ModelSelect2Widget(
    #                                 model=Invoice,search_fields=['name__icontains'],dependent_fields={'customer':'customer'}),
    # )
    invoice=forms.ModelChoiceField(
                                    queryset=Invoice.objects.all(),
                                    widget=Select2Widget,
    )
    class Meta:
        model=ReceiptLine
        fields=['invoice','amount']

ReceiptLineFormSet=inlineformset_factory(Receipt,ReceiptLine,
    fields=('invoice','amount','receipt'),extra=0,can_delete=True,form=ReceiptLineForm)
