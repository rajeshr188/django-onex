from django import forms
import datetime
from tempus_dominus.widgets import DatePicker, TimePicker, DateTimePicker
from .models import Invoice, InvoiceItem, Receipt,ReceiptLine
from django_select2.forms import Select2Widget,ModelSelect2Widget,ModelSelect2MultipleWidget
from contact.models import Customer
from product.models import ProductVariant,Stree,Stock
from django.forms.models import inlineformset_factory
from django.db.models import Q
from mptt.forms import TreeNodeChoiceField

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
        fields = ['created','rate', 'balancetype', 'paymenttype', 'balance','term', 'customer','status']

class InvoiceItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(
                        queryset = Stock.objects.all().order_by('-Qih','-Wih'),
                        widget = Select2Widget,
                        )
    class Meta:
        model = InvoiceItem
        fields = ['invoice','is_return','product','quantity','weight', 'less_stone','touch','wastage','makingcharge','total',]

    # def save(self,commit = True):
    #     invoiceitem = super(InvoiceItemForm,self).save(commit = False)
    #     if invoiceitem.id:
    #         if any( x in self.changed_data for x in ['product','quantity','weight']):
    #             InvoiceItem.objects.get(id = invoiceitem.id).delete()
    #     if commit:
    #         try:
    #             invoiceitem.save()
    #         except Exception:
    #             raise Exception("failed From Model Save")
    #     return invoiceitem

InvoiceItemFormSet=inlineformset_factory(Invoice,InvoiceItem,
    fields=('is_return','product','quantity',
    'weight','less_stone', 'touch', 'wastage','makingcharge','total', 'invoice'),
    form = InvoiceItemForm,extra=2,can_delete=True)

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

    def save(self,commit = True):
        instance = super(ReceiptForm,self).save(commit=False)
        if instance.id:
            print('deleting previous receiptlines')
            ReceiptLine.objects.filter(receipt = instance.id).delete()
        if commit:
            print(f"Receipt ModelForm Save()commit:{commit}")

            print("saving receipt and updating status")
            instance.save()
            print("allotting")
            instance.allot()
        return instance

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
