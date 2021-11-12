import re
from django import forms
import datetime
from tempus_dominus.widgets import DateTimePicker
from .models import Invoice, InvoiceItem, Receipt,ReceiptLine,ReceiptItem
from django_select2.forms import Select2Widget
from contact.models import Customer
from approval.models import Approval
from product.models import Stock
from django.forms.models import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset,Row,Column,ButtonHolder, Submit
from utils.custom_layout_object import *
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
    customer=forms.ModelChoiceField(queryset=Customer.objects.all(),
                widget = Select2Widget)
    approval = forms.ModelChoiceField(queryset = Approval.objects.all(),
                widget = Select2Widget,required = False)
    class Meta:
        model = Invoice
        fields = ['created','approval','rate','is_gst', 'balancetype',
                    'metaltype','gross_wt','net_wt','balance','total','term',
                     'customer','status','posted']

    def __init__(self, *args, **kwargs):
        super(InvoiceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-group'
        self.helper.label_class = 'col-md-12 form-label'
        self.helper.field_class = 'col-md-12'
        self.helper.layout = Layout(
            Row(
                Column(Field('created', css_class='form-control'),
                       css_class='form-group col-md-3 mb-0'),
                Column(Field('customer', css_class='form-control'),
                       css_class='form-group col-md-3 mb-0'),
                Column(Field('is_gst'), css_class='form-group col-md-3 mb-0'),
                css_class='form-row'),
            Row(
                Column('balancetype', css_class='form-group col-md-3 mb-0'),
                Column('metaltype', css_class='form-group col-md-3 mb-0'),
                Column('rate', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'),
            Row(Column(Field('approval', css_class='form-group col-md-3 mb-0')),
                css_class='form-row'),
            Fieldset('Add items',
                     Formset('items')),
            Row(
                Column(Field('gross_wt', css_class='form-control'),
                       css_class='form-group col-md-3 mb-0'),
                Column(Field('net_wt', css_class='form-control'),
                       css_class='form-group col-md-3 mb-0'),
                Column(Field('total', css_class='form-control'),
                       css_class='form-group col-md-3 mb-0'),
                css_class='form-row'),
            Row(
                Column('term', css_class='form-group col-md-3 mb-0'),
                Column('balance', css_class='form-group col-md-3 mb-0'),
                Column('status', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'),
            ButtonHolder(Submit('submit', 'save'))
        )

class InvoiceItemForm(forms.ModelForm):
    # TODO add filter to show only stock with qty and wt >0
    # product = forms.ModelChoiceField(
    #                     queryset = Stock.objects.filter(Q(wt__gt = 0)&Q(qty__gt = 0)),
    #                     widget = Select2Widget)
    class Meta:
        model = InvoiceItem
        fields = ['invoice','is_return','product','quantity','weight', 'less_stone',
        'net_wt','touch','wastage','makingcharge','total',]

InvoiceItemFormSet = inlineformset_factory(
    Invoice, InvoiceItem, form=InvoiceItemForm, extra=1, can_delete=True,
    fields=('is_return','product','quantity',
    'weight','less_stone', 'touch', 'wastage','makingcharge','net_wt','total', 'invoice'),
    )

class ReceiptForm(forms.ModelForm):
    customer=forms.ModelChoiceField(queryset=Customer.objects.filter(type='Wh'),widget=Select2Widget)
    created = forms.DateTimeField(
        widget=DateTimePicker(
            options={
                'defaultDate': (datetime.date.today()).strftime('%Y-%m-%d'),
                'minDate': '2013-02-07',#(datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),  # Tomorrow
                'useCurrent': True,
                'collapse': False},
            attrs={
               'append': 'fa fa-calendar',
               'input_toggle': False,
               'icon_toggle': True}),)
    class Meta:
        model = Receipt
        fields = ['created','customer','type', 
                    'rate','total', 'description','status']

class ReceiptLineForm(forms.ModelForm):
    invoice=forms.ModelChoiceField(queryset=Invoice.objects.all(),
                                    widget=Select2Widget)
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
