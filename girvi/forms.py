from django import forms
from .models import License, Loan, Release
from django_select2.forms import Select2Widget
from contact.models import Customer
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field,Div
from crispy_forms.bootstrap import (
    AppendedText,PrependedText, PrependedAppendedText, FormActions)
class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        fields = ['name', 'type', 'shopname', 'address', 'phonenumber', 'propreitor']


class LoanForm(forms.ModelForm):
    customer=forms.ModelChoiceField(queryset=Customer.objects.all(),widget=Select2Widget)
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-sm-2'
    helper.field_class = 'col-sm-4'
    helper.layout = Layout(
        Field('license', css_class='input-sm'),
        Field('customer', css_class='input-sm'),
        Field('loanid', css_class='input-sm'),
        Field('created',css_class='input-sm'),
        Field('itemtype', css_class='input-sm'),
        Field('itemdesc', css_class='input-sm'),
        Field('itemweight', css_class='input-sm'),
        Field('loanamount', css_class='input-sm'),
        Field('itemvalue', css_class='input-sm'),
        AppendedText('interestrate', '%',css_class='input-sm'),
        FormActions(Submit('Submit', 'Submit', css_class='btn-primary'))
    )
    class Meta:
        model = Loan
        fields = [ 'license', 'customer','loanid','created', 'itemtype', 'itemdesc', 'itemweight','loanamount', 'itemvalue',  'interestrate']

class ReleaseForm(forms.ModelForm):
    customer=forms.ModelChoiceField(queryset=Customer.objects.all(),widget=Select2Widget)
    loan=forms.ModelChoiceField(queryset=Loan.objects.all(),widget=Select2Widget)
    class Meta:
        model = Release
        fields = ['releaseid','customer','loan', 'interestpaid',]
