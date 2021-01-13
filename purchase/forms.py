from django import forms
from .models import Invoice, InvoiceItem, Payment,PaymentLine
from django_select2.forms import Select2Widget,ModelSelect2Widget
from contact.models import Customer
from product.models import ProductVariant
from django.forms.models import inlineformset_factory
from django.db.models import Q
from tempus_dominus.widgets import DatePicker, TimePicker, DateTimePicker
from datetime import datetime

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
        fields = ['created','rate', 'balancetype', 'paymenttype', 'balance', 'supplier','status','posted']


class InvoiceItemForm(forms.ModelForm):
    product=forms.ModelChoiceField(queryset=ProductVariant.objects.all(),widget=Select2Widget)
    class Meta:
        model = InvoiceItem
        fields = ['weight', 'touch', 'total', 'is_return', 'quantity', 'product', 'invoice','makingcharge']

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

InvoiceItemFormSet=inlineformset_factory(Invoice,InvoiceItem,
    fields=('is_return','product','quantity','weight', 'touch',
    'makingcharge','total', 'invoice'),form = InvoiceItemForm,extra=2,can_delete=True)

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
        fields = ['supplier','created','type', 'weight','touch','nettwt','rate','total', 'description','status']

class PaymentLineForm(forms.ModelForm):

    invoice=forms.ModelChoiceField(
                                    queryset=Invoice.objects.filter(Q(status="Unpaid")|Q(status="PartiallyPaid")),
                                    widget=Select2Widget,
    )
    class Meta:
        model=PaymentLine
        fields=['invoice','amount']

PaymentLineFormSet=inlineformset_factory(Payment,PaymentLine,
    fields=('invoice','amount','payment'),extra=0,can_delete=True,form=PaymentLineForm)
