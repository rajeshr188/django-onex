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

from .models import Adjustment, License, Loan, Release, Series


class CustomSelect2Widget(Select2Widget, Select2Mixin):
    def __init__(self, attrs=None, **kwargs):
        default_attrs = {"class": "select2", "style": "width: 100%;"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs, **kwargs)


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
            # widget = CustomSelect2Widget(
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = "modal-content"
        self.helper.form_action = reverse_lazy("girvi_loan_create")
        self.helper.attrs = {
            # "hx-post": reverse_lazy("girvi_loan_create"),
            # "hx-target": "#loancontent",
            # "hx-swap": "innerHTML",
            # "hx-push-url": "true",
        }
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


Loan_formset = modelformset_factory(
    Loan,
    fields=(
        "id",
        "series",
        "lid",
        "created",
        "customer",
        "loanamount",
        "itemtype",
        "itemdesc",
        "interestrate",
        "itemweight",
    ),
    extra=0,
)


Release_formset = modelformset_factory(
    Release, ReleaseForm, fields=("releaseid", "loan", "interestpaid")
)
