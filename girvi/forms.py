from django import forms
from django.forms import formset_factory
import datetime
from tempus_dominus.widgets import DatePicker, TimePicker, DateTimePicker
from .models import License, Loan, Release
from django_select2.forms import Select2Widget,ModelSelect2Widget
from contact.models import Customer

class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        fields = ['name', 'type', 'shopname', 'address', 'phonenumber', 'propreitor']


class LoanForm(forms.ModelForm):
    customer=forms.ModelChoiceField(queryset=Customer.objects.filter(type='Re'),widget=Select2Widget)

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
    created = forms.DateTimeField(
        widget=DateTimePicker(
            options={
                'minDate': '2010-01-01',
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
    # customer = forms.ModelChoiceField(queryset=Customer.objects.filter(type='Re'),
    #                                     widget=Select2Widget)
    customer = forms.ModelChoiceField(queryset = Customer.objects.filter(type='Re'),
                                        widget=ModelSelect2Widget(
                                        queryset = Customer.objects.filter(type='Re'),
                                        model=Customer,
                                        search_fields=['name__icontains'],
        ))
    loan = forms.ModelChoiceField(queryset=Loan.objects.all(),
                                    widget=ModelSelect2Widget(
                                    model=Loan,
                                    search_fields=['loanid_icontains'],
                                    dependent_fields={'customer':'customer'}),
                                    )

    class Meta:
        model = Release
        fields = ['releaseid','customer','loan', 'interestpaid',]

Release_formset = formset_factory(ReleaseForm,extra=1)
