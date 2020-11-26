from django import forms
from django.forms import modelformset_factory
from datetime import datetime,timezone
from tempus_dominus.widgets import DatePicker, TimePicker, DateTimePicker
from .models import License, Loan, Release, Adjustment,Series
from django_select2.forms import Select2Widget,ModelSelect2Widget,Select2MultipleWidget
from django.forms.widgets import CheckboxSelectMultiple
from contact.models import Customer

class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        fields = ['name', 'type', 'shopname', 'address', 'phonenumber', 'propreitor']

class SeriesForm(forms.ModelForm):
    class Meta:
        model = Series
        fields = ['name','license']

class LoanForm(forms.ModelForm):
    customer=forms.ModelChoiceField(queryset=Customer.objects.filter(type='Re'),widget=Select2Widget)
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
        model = Loan
        fields = [ 'series', 'customer','lid','created', 'itemtype', 'itemdesc', 'itemweight','loanamount', 'interestrate']

class LoanRenewForm(forms.Form):
    amount = forms.IntegerField()
    interest = forms.IntegerField()

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

    class Meta:
        model = Release
        fields = ['releaseid','loan', 'interestpaid',]

class BulkReleaseForm(forms.Form):
    date = forms.DateTimeField(
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
    loans = forms.ModelMultipleChoiceField(
        widget=Select2MultipleWidget,
        queryset=Loan.unreleased.all())

class AdjustmentForm(forms.ModelForm):
    created = forms.DateTimeField(
        widget=DateTimePicker(
            options={
                'defaultDate': (datetime.now()).strftime("%m/%d/%Y, %H:%M:%S"),
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

    loan = forms.ModelChoiceField(queryset=Loan.unreleased.all(),
                                    widget=ModelSelect2Widget(
                                    model=Loan,
                                    queryset = Loan.unreleased.all(),
                                    search_fields=['loanid_icontains'],
                                    # dependent_fields={'customer':'customer'}
        ))

    class Meta:
        model = Adjustment
        fields = ['loan', 'amount_received','as_interest']

Loan_formset = modelformset_factory(Loan,fields = ('id','series','lid','created',
                                    'customer','loanamount','itemtype',
                                    'itemdesc','interestrate','itemweight'),
                                    extra=0)



Release_formset = modelformset_factory(Release,ReleaseForm,fields=('releaseid','loan','interestpaid'))
