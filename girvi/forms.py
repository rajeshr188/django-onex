from crispy_bootstrap5.bootstrap5 import FloatingField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AutocompleteSelect
from django.contrib.postgres.forms import DateRangeField
from django.forms import DateTimeInput, modelformset_factory
from django.urls import reverse_lazy
from django_select2 import forms as s2forms
from django_select2.forms import (ModelSelect2Widget, Select2Mixin,
                                  Select2MultipleWidget, Select2Widget)

from contact.forms import CustomerWidget
from contact.models import Customer
from product.models import ProductVariant

from .models import Adjustment, License, Loan, LoanItem, Release, Series


class LoansWidget(s2forms.ModelSelect2Widget):
    search_fields = ["loanid__icontains"]


class MultipleLoansWidget(s2forms.ModelSelect2MultipleWidget):
    search_fields = ["loanid__icontains"]


class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        fields = ["name", "type", "shopname", "address", "phonenumber", "propreitor"]


class SeriesForm(forms.ModelForm):
    class Meta:
        model = Series
        fields = ["name", "license"]


class LoanForm(forms.ModelForm):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        widget=CustomerWidget(
            select2_options={
                "width": "100%",
            }
        ),
    )
    # customer = forms.ModelChoiceField(
    #     queryset=Customer.objects.all(),
    #     widget=AutocompleteSelect(Loan._meta.get_field('customer'), admin.site,
    #     attrs={'data-dropdown-auto-width': 'true'}
    #     )
    # )
    series = forms.ModelChoiceField(
        queryset=Series.objects.exclude(is_active=False),
        # widget = ModelSelect2Widget(
        widget=forms.Select(
            attrs={
                "hx-get": reverse_lazy("girvi_series_next_loanid"),
                "hx-target": "#div_id_lid",
                "hx-trigger": "change",
                "hx-swap": "innerHTML",
            }
        ),
    )

    created = forms.DateTimeField(
        input_formats=["%d/%m/%Y %H:%M"],
        widget=forms.TextInput(
            attrs={"type": "datetime-local", "data-date-format": "DD MMMM YYYY"}
        ),
    )

    itemdesc = forms.CharField(
        widget=forms.Textarea,
    )

    class Meta:
        model = Loan
        fields = [
            "series",
            "customer",
            "lid",
            "created",
            "itemtype",
            "itemdesc",
            "itemweight",
            "loanamount",
            "interestrate",
        ]
    def clean(self):
        cleaned_data = super().clean()
        loanid = Series.objects.get(id = self.cleaned_data['series'].id).name +str(self.cleaned_data['lid'])
        if Loan.objects.filter(loanid=loanid).exists():
            raise forms.ValidationError("A loan with this loanID already exists.")
        

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        # self.helper.form_action = reverse_lazy("girvi_loan_create")
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column(FloatingField("series"), css_class="form-group col-md-3 mb-0"),
                Column(FloatingField("lid"), css_class="form-group col-md-3 mb-0"),
                Column(
                    FloatingField("created"), css_class="form-group col-md-3 mb-0 date"
                ),
                css_class="form-row",
            ),
            Row(
                Column("customer", css_class="form-group col-md-3 mb-0"),
                Column(FloatingField("itemtype"), css_class="form-group col-md-3 mb-0"),
                Column(
                    FloatingField("interestrate"), css_class="form-group col-md-3 mb-0"
                ),
                css_class="form-row",
            ),
            Row(
                Column(
                    FloatingField("itemweight"), css_class="form-group col-md-3 mb-0"
                ),
                Column(
                    FloatingField("loanamount"), css_class="form-group col-md-3 mb-0"
                ),
                Column(FloatingField("itemdesc"), css_class="form-group col-md-3 mb-0"),
                css_class="form-row",
            ),
            # Submit("submit", "Submit"),  
        )

class LoanRenewForm(forms.Form):
    amount = forms.IntegerField()
    interest = forms.IntegerField()


class LoanItemForm(forms.ModelForm):
    item = forms.ModelChoiceField(
        queryset=ProductVariant.objects.all(),
        widget=ModelSelect2Widget(
            search_fields=["name__icontains"],
            select2_options={
                "width": "100%",
            },
        ),
    )

    class Meta:
        model = LoanItem
        fields = ["item", "qty", "weight", "loanamount", "interestrate", "interest"]


class ReleaseForm(forms.ModelForm):
    created = forms.DateTimeField(
        widget=DateTimeInput(attrs={"type": "datetime-local"}),
    )
    loan = forms.ModelChoiceField(widget=LoansWidget, queryset=Loan.unreleased.all())

    class Meta:
        model = Release
        fields = [
            "releaseid",
            "loan",
            "interestpaid",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column("releaseid", css_class="form-group col-md-3 mb-0"),
                Column("created", css_class="form-group col-md-3 mb-0"),
                css_class="form-row",
            ),
            Row(
                Column("loan", css_class="form-group col-md-3 mb-0"),
                Column("interestpaid", css_class="form-group col-md-3 mb-0"),
                css_class="form-row",
            ),
            Submit("submit", "Submit"),
        )


class BulkReleaseForm(forms.Form):
    date = forms.DateTimeField(widget=DateTimeInput(attrs={"type": "datetime-local"}))
    loans = forms.ModelMultipleChoiceField(
        widget=MultipleLoansWidget, queryset=Loan.unreleased.all()
    )
    # principal = forms.IntegerField()
    # interest = forms.IntegerField()
    # total = forms.IntegerField()
    # total_received = forms.IntegerField()


class PhysicalStockForm(forms.Form):
    date = forms.DateTimeField(widget=DateTimeInput(attrs={"type": "datetime-local"}))
    loans = forms.ModelMultipleChoiceField(
        widget=MultipleLoansWidget, queryset=Loan.objects.filter(series__is_active=True)
    )


class AdjustmentForm(forms.ModelForm):
    created = forms.DateTimeField(
        widget=DateTimeInput(attrs={"type": "datetime-local"})
    )

    loan = forms.ModelChoiceField(
        queryset=Loan.unreleased.all(),
        widget=ModelSelect2Widget(
            model=Loan,
            queryset=Loan.unreleased.all(),
            search_fields=["loanid_icontains"],
            # dependent_fields={'customer':'customer'}
        ),
    )

    class Meta:
        model = Adjustment
        fields = ["loan", "amount_received", "as_interest"]