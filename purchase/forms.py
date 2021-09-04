from django import forms
from .models import Invoice, InvoiceItem, Payment, PaymentItem,PaymentLine
from django_select2.forms import Select2Widget,ModelSelect2Widget
from contact.models import Customer
from product.models import ProductVariant
from django.forms.models import inlineformset_factory
from django.db.models import Q
from tempus_dominus.widgets import DateTimePicker
from datetime import datetime
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset, Div,Row,Column, HTML, ButtonHolder, Submit
from utils.custom_layout_object import *

class InvoiceForm(forms.ModelForm):
    supplier=forms.ModelChoiceField(queryset=Customer.objects.exclude(type='Re'),widget=Select2Widget)
    created = forms.DateTimeField(
        widget=DateTimePicker(
            options={
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
        model = Invoice
        fields = ['created','rate','is_gst','balancetype','metaltype',
                    'gross_wt','net_wt','total',
                     'balance', 'supplier','term','status','posted']

class CrispyInvoiceForm(InvoiceForm):
    def __init__(self, *args, **kwargs):
        super(InvoiceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-group'
        self.helper.label_class = 'col-md-6 create-label'
        self.helper.field_class = 'col-md-12'
        self.helper.layout = Layout(
            Row(
                Column('created', css_class='form-group col-md-3 mb-0'),
                Column('supplier', css_class='form-group col-md-3 mb-0'),
                Column('is_gst', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('balancetype', css_class='form-group col-md-3 mb-0'),
                Column('metaltype', css_class='form-group col-md-3 mb-0'),
                Column('rate', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Fieldset('Add items',
                             Formset('items')),
            Row(
                Column('gross_wt', css_class='form-group col-md-3 mb-0'),
                Column('net_wt', css_class='form-group col-md-3 mb-0'),
                Column('total', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('term', css_class='form-group col-md-3 mb-0'),
                Column('balance', css_class='form-group col-md-3 mb-0'),
                Column('status', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
                ),
            ButtonHolder(Submit('submit', 'save'))

            
        )

class InvoiceItemForm(forms.ModelForm):
    product=forms.ModelChoiceField(
                queryset=ProductVariant.objects.all(),
                widget=Select2Widget)
    class Meta:
        model = InvoiceItem
        fields = ['weight', 'touch', 'total', 'is_return','huid', 'quantity', 'product', 'invoice','makingcharge','net_wt']

    # def save(self,commit = True):
    #     print("in form.save()")
    #     invoiceitem = super(InvoiceItemForm,self).save(commit = False)
    #     if invoiceitem.id:
    #
    #         if any( x in self.changed_data for x in ['product','quantity','weight']):
    #             print("deleting line items that changed")
    #             InvoiceItem.objects.get(id = invoiceitem.id).delete()
    #
    #     if commit:
    #         try:
    #             invoiceitem.save()
    #         except Exception:
    #             raise Exception("failed From Model Save")
    #     return invoiceitem


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
