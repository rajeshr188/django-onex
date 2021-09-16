from django import forms
from .models import Invoice, InvoiceItem, Payment, PaymentItem,PaymentLine
from django_select2.forms import Select2Widget
from contact.models import Customer
from product.models import ProductVariant
from django.forms.models import inlineformset_factory
from django.db.models import Q
from tempus_dominus.widgets import DateTimePicker
from datetime import datetime
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset,Row,Column,ButtonHolder, Submit
# from crispy_bootstrap5.bootstrap5 import FloatingField
from utils.custom_layout_object import *

class InvoiceForm(forms.ModelForm):
    supplier=forms.ModelChoiceField(queryset=Customer.objects.exclude(type='Re'),
                    widget=Select2Widget)
    created = forms.DateTimeField(
        widget=DateTimePicker(
            options={
                'useCurrent': True,
                'collapse': False,},
            attrs={
               'append': 'fa fa-calendar',
               'input_toggle': False,
               'icon_toggle': True,}),)
    class Meta:
        model = Invoice
        fields = ['created','rate','is_gst','balancetype','metaltype',
                    'gross_wt','net_wt','total',
                     'balance', 'supplier','term','status','posted']

    def __init__(self, *args, **kwargs):
        super(InvoiceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-group'
        self.helper.label_class = 'col-md-6 create-label'
        self.helper.field_class = 'col-md-12'
        self.helper.layout = Layout(
            Row(
                Column(Field('created',css_class ='form-control'), css_class='form-group col-md-3 mb-0'),
                Column(Field('supplier',css_class='form-control'), css_class='form-group col-md-3 mb-0'),
                Column(Field('is_gst'), css_class='form-group col-md-3 mb-0'),
                css_class='form-row'),
            Row(
                Column('balancetype', css_class='form-group col-md-3 mb-0'),
                Column('metaltype', css_class='form-group col-md-3 mb-0'),
                Column('rate', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'),
            Fieldset('Add items',
                             Formset('items')),
            Row(
                Column(Field('gross_wt',css_class='form-control'), css_class='form-group col-md-3 mb-0'),
                Column(Field('net_wt',css_class='form-control'), css_class='form-group col-md-3 mb-0'),
                Column(Field('total',css_class='form-control'), css_class='form-group col-md-3 mb-0'),
                css_class='form-row'),
            Row(
                Column('term', css_class='form-group col-md-3 mb-0'),
                Column('balance', css_class='form-group col-md-3 mb-0'),
                Column('status', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'),
            ButtonHolder(Submit('submit', 'save'))      
        )

class InvoiceUpdateForm(InvoiceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout.fields[-1].value = "Save Changes"
class InvoiceItemForm(forms.ModelForm):
    product=forms.ModelChoiceField(
                queryset=ProductVariant.objects.all(),
                widget=Select2Widget)
    class Meta:
        model = InvoiceItem
        fields = ['weight', 'touch', 'total', 'is_return','huid', 'quantity', 'product', 'invoice','makingcharge','net_wt']

InvoiceItemFormSet = inlineformset_factory(Invoice, InvoiceItem,form=InvoiceItemForm,
    fields=['is_return','huid','product','quantity','weight', 'touch',
    'net_wt','makingcharge','total', 'invoice'],extra=1,can_delete=True)

class PaymentForm(forms.ModelForm):
    created = forms.DateTimeField(
        widget=DateTimePicker(
            options={
                'defaultDate': (datetime.now()).strftime("%m/%d/%Y, %H:%M:%S"),
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
    supplier=forms.ModelChoiceField(queryset=Customer.objects.all(),widget=Select2Widget)
    class Meta:
        model = Payment
        fields = ['supplier','created','type','rate','total', 'description','status']

class PaymentLineForm(forms.ModelForm):

    invoice=forms.ModelChoiceField(
                                    queryset=Invoice.objects.filter(Q(status="Unpaid")|Q(status="PartiallyPaid")),
                                    widget=Select2Widget,
    )
    class Meta:
        model=PaymentLine
        fields=['invoice','amount']

class PaymentItemForm(forms.ModelForm):
    class Meta:
        models = PaymentItem
        fields = '__all__'

PaymentItemFormSet=inlineformset_factory(Payment,PaymentItem,
    fields=('weight','touch','nettwt','amount','payment'),extra=1,can_delete=True,form=PaymentItemForm)

PaymentLineFormSet=inlineformset_factory(Payment,PaymentLine,
    fields=('invoice','amount','payment'),extra=1,can_delete=True,form=PaymentLineForm)
