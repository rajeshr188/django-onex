from django import forms
import datetime
from tempus_dominus.widgets import DatePicker, TimePicker, DateTimePicker
from .models import License, Loan, Release
from django_select2.forms import Select2Widget,ModelSelect2Widget
from contact.models import Customer
# from crispy_forms.helper import FormHelper
# from crispy_forms.layout import Submit, Layout, Field,Div
# from crispy_forms.bootstrap import (
#     AppendedText,PrependedText, PrependedAppendedText, FormActions)

class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        fields = ['name', 'type', 'shopname', 'address', 'phonenumber', 'propreitor']


class LoanForm(forms.ModelForm):
    customer=forms.ModelChoiceField(queryset=Customer.objects.all(),widget=Select2Widget)

    created = forms.DateTimeField(
        widget=DateTimePicker(
            options={
                'minDate': '2010-01-01',#(datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),  # Tomorrow
                'useCurrent': True,
                'collapse': True,
            },
            attrs={
               'append': 'fa fa-calendar',
               'input_toggle': False,
               'icon_toggle': True,
            }
        ),
    )
    
    class Meta:
        model = Loan
        fields = [ 'license', 'customer','loanid','created', 'itemtype', 'itemdesc', 'itemweight','loanamount', 'itemvalue',  'interestrate']

class ReleaseForm(forms.ModelForm):
    customer=forms.ModelChoiceField(queryset=Customer.objects.all(),widget=Select2Widget)
    loan=forms.ModelChoiceField(queryset=Loan.objects.all(),
                                    widget=ModelSelect2Widget(
                                    model = Loan,search_fields=['name__icontains'],dependent_fields={'customer':'customer'}
                                    )
                                ),
        # invoice=forms.ModelChoiceField(
        #                                 queryset=Invoice.objects.all(),
        #                                 widget=ModelSelect2Widget(
        #                                 model=Invoice,search_fields=['name__icontains'],dependent_fields={'customer':'customer'}),
        # )
    class Meta:
        model = Release
        fields = ['releaseid','customer','loan', 'interestpaid',]
