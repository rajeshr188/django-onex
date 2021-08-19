from django import forms
import datetime
from tempus_dominus.widgets import DateTimePicker
from .models import Invoice, InvoiceItem, Receipt,ReceiptLine,ReceiptItem
from django_select2.forms import Select2Widget
from contact.models import Customer
from product.models import Stock
from django.forms.models import inlineformset_factory


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
    customer=forms.ModelChoiceField(queryset=Customer.objects.all(),
                widget=Select2Widget)
    class Meta:
        model = Invoice
        fields = ['created','approval','rate','is_gst', 'balancetype',
                    'metaltype','gross_wt','net_wt','balance','term',
                     'customer','status','posted']

class InvoiceItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(
                        queryset = Stock.objects.filter(status = "Available"),
                        widget = Select2Widget,
                        )
    class Meta:
        model = InvoiceItem
        fields = ['invoice','is_return','product','quantity','weight', 'less_stone','net_wt','touch','wastage','makingcharge','total',]

InvoiceItemFormSet=inlineformset_factory(Invoice,InvoiceItem,
    fields=('is_return','product','quantity',
    'weight','less_stone', 'touch', 'wastage','makingcharge','net_wt','total', 'invoice'),
    form = InvoiceItemForm,extra=1,can_delete=True)

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
        fields = ['created','customer','type', 
                    # 'weight','touch','nettwt',
                    'rate','total', 'description','status']

class ReceiptLineForm(forms.ModelForm):
    invoice=forms.ModelChoiceField(
                                    queryset=Invoice.objects.all(),
                                    widget=Select2Widget,
    )
    class Meta:
        model=ReceiptLine
        fields=['invoice','amount']

ReceiptLineFormSet=inlineformset_factory(Receipt,ReceiptLine,
    fields=('invoice','amount','receipt'),extra=0,can_delete=True,form=ReceiptLineForm)


class ReceiptItemForm(forms.ModelForm):
    class Meta:
        models = ReceiptItem
        fields = '__all__'


ReceiptItemFormSet = inlineformset_factory(Receipt, ReceiptItem,
    fields=('weight','touch','nettwt', 'amount','receipt'), extra=1, can_delete=True, form=ReceiptItemForm)
