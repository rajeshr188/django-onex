from django import forms
from django.forms import modelformset_factory
from datetime import datetime
from tempus_dominus.widgets import DateTimePicker
from .models import License, Loan, Release, Adjustment,Series
from django_select2.forms import Select2Widget,ModelSelect2Widget,Select2MultipleWidget
from contact.models import Customer
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        fields = ['name', 'type', 'shopname', 'address', 'phonenumber', 'propreitor']

class SeriesForm(forms.ModelForm):
    class Meta:
        model = Series
        fields = ['name','license']

class LoanForm(forms.ModelForm):
    customer=forms.ModelChoiceField(queryset=Customer.objects.all(),widget=Select2Widget)
    series = forms.ModelChoiceField(queryset = Series.objects.exclude(is_active=False),
                    # widget = Select2Widget
                    )
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('series', css_class='form-group col-md-3 mb-0'),
                Column('lid', css_class='form-group col-md-3 mb-0'),
                Column('created', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('customer', css_class='form-group col-md-3 mb-0'),
                Column('itemtype', css_class='form-group col-md-3 mb-0'),
                Column('interestrate', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),

            Row(
                Column('itemweight', css_class='form-group col-md-3 mb-0'),
                Column('loanamount', css_class='form-group col-md-3 mb-0'),
                Column('itemdesc', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
        
            Submit('submit', 'Submit')
        )

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('releaseid', css_class='form-group col-md-3 mb-0'),
                Column('created', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('loan', css_class='form-group col-md-3 mb-0'),
                Column('interestpaid', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Submit')
        )

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

class PhysicalStockForm(forms.Form):
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
        queryset=Loan.objects.filter(series__is_active=True))
    

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
