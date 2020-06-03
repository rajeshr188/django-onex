from django import forms
from django.forms import modelformset_factory
from datetime import datetime,timezone
from tempus_dominus.widgets import DatePicker, TimePicker, DateTimePicker
from .models import License, Loan, Release, Adjustment
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
                'defaultDate':datetime.now(timezone.utc),
                'minDate': '2018-01-01',#(datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),  # Tomorrow
                'useCurrent': True,
                'collapse': False,
            },
            attrs={
               'append': 'fa fa-calendar',
               'icon_toggle': True,
            }
        ),
    )

    class Meta:
        model = Loan
        fields = [ 'license', 'customer','loanid','created', 'itemtype', 'itemdesc', 'itemweight','loanamount', 'interestrate']

class ReleaseForm(forms.ModelForm):
    created = forms.DateTimeField(
        widget=DateTimePicker(
            options={
                'defaultDate': (datetime.now(timezone.utc)).strftime("%m/%d/%Y, %H:%M:%S"),
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

    # loan = forms.ModelChoiceField(queryset=Loan.unreleased.all(),
    #                                 widget = Select2Widget,
    #                                 # widget=ModelSelect2Widget(
    #                                 # model=Loan,
    #                                 # queryset = Loan.unreleased.all(),
    #                                 # search_fields=['loanid_icontains'],)
    #                                 )

    class Meta:
        model = Release
        fields = ['releaseid','loan', 'interestpaid',]

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

Loan_formset = modelformset_factory(Loan,fields = ('loanid','created',
                                    'customer','loanamount','itemtype',
                                    'itemdesc','interestrate','itemweight'),
                                    extra=2)



Release_formset = modelformset_factory(Release,ReleaseForm,fields=('releaseid','loan','interestpaid'))
