from datetime import datetime
from decimal import Decimal

from crispy_bootstrap5.bootstrap5 import FloatingField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AutocompleteSelect
from django.urls import reverse_lazy
from django.utils import timezone
from django_select2 import forms as s2forms
from django_select2.forms import (ModelSelect2Widget, Select2Mixin,
                                  Select2MultipleWidget, Select2Widget)

from contact.forms import CustomerWidget
from contact.models import Customer
from product.models import ProductVariant, Rate

from .models import (Adjustment, License, Loan, LoanItem, Release, Series,
                     Statement, StatementItem)


class LoansWidget(s2forms.ModelSelect2Widget):
    search_fields = ["loanid__icontains"]


class SeriesWidget(s2forms.ModelSelect2Widget):
    search_fields = ["name__icontains"]


class MultipleLoansWidget(s2forms.ModelSelect2MultipleWidget):
    search_fields = ["loanid__icontains"]


class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        fields = ["name", "type", "shopname", "address", "phonenumber", "propreitor"]


class SeriesForm(forms.ModelForm):
    class Meta:
        model = Series
        fields = ["name", "license", "is_active"]


class LoanForm(forms.ModelForm):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        widget=CustomerWidget(),
    )
    # customer = forms.ModelChoiceField(
    #     queryset=Customer.objects.all(),
    #     widget=AutocompleteSelect(Loan._meta.get_field('customer'), admin.site,
    #     attrs={'data-dropdown-auto-width': 'true'}
    #     )
    # )

    series = forms.ModelChoiceField(
        queryset=Series.objects.exclude(is_active=False),
        widget=forms.Select(
            attrs={
                "hx-get": reverse_lazy("girvi:girvi_series_next_loanid"),
                "hx-target": "#div_id_lid",
                "hx-trigger": "change",
                "hx-swap": "innerHTML",
                "autofocus": True,
            }
        ),
    )

    created = forms.DateTimeField(
        input_formats=["%d/%m/%Y %H:%M"],
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local",
                "data-date-format": "DD MMMM YYYY",
                "max": datetime.now(),
            }
        ),
    )

    class Meta:
        model = Loan
        fields = [
            "loan_type",
            "series",
            "customer",
            "pic",
            "lid",
            "created",
        ]

    def clean_created(self):
        cleaned_data = super().clean()
        my_date = cleaned_data.get("created")

        if my_date and my_date > timezone.now():
            raise forms.ValidationError("Date cannot be in the future.")

        return my_date

    def clean(self):
        cleaned_data = super().clean()

        if not self.cleaned_data["series"].is_active:
            raise forms.ValidationError(
                f"Series {self.cleaned_data['series'].name}Inactive"
            )

        # generate loan id when created
        loanid = Series.objects.get(id=self.cleaned_data["series"].id).name + str(
            self.cleaned_data["lid"]
        )
        # # in update mode, check if loanid is changed
        if self.instance.loanid and self.instance.loanid == loanid:
            return cleaned_data
        # when created, check if loanid already exists
        if Loan.objects.filter(loanid=loanid).exists():
            raise forms.ValidationError("A loan with this loanID already exists.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.help_text_inline = True
        self.helper.layout = Layout(
            Row(
                Column(FloatingField("loan_type"), css_class="col-md"),
                Column(FloatingField("created"), css_class="col-md date"),
                css_class="row",
            ),
            Row(
                Column(FloatingField("series"), css_class="col-md"),
                Column(FloatingField("lid"), css_class="col-md"),
                css_class="row",
            ),
            Row(
                Column("customer", css_class="col-md"),
                css_class="row",
            ),
        )


class LoanRenewForm(forms.Form):
    amount = forms.IntegerField()
    interest = forms.IntegerField()


class LoanItemForm(forms.ModelForm):
    # item = forms.ModelChoiceField(
    #     queryset=ProductVariant.objects.all(),
    #     widget=ModelSelect2Widget(
    #         search_fields=["name__icontains"],
    #         select2_options={
    #             "width": "100%",
    #         },
    #     ),
    # )
    itemdesc = forms.CharField(
        widget=forms.Textarea(attrs={"autofocus": True, "rows": "3"}),
    )
    itemtype = forms.ChoiceField(
        choices=(("Gold", "Gold"), ("Silver", "Silver"), ("Bronze", "Bronze")),
        widget=forms.Select(
            attrs={
                "hx-get": reverse_lazy("girvi:girvi_get_interestrate"),
                "hx-target": "#div_id_interestrate",
                "hx-trigger": "change,load",
                "hx-swap": "innerHTML",
            }
        ),
    )

    class Meta:
        model = LoanItem
        fields = [
            "pic",
            "itemdesc",
            "itemtype",
            "quantity",
            "weight",
            "purity",
            "loanamount",
            "interestrate",
        ]

    def clean(self):
        cleaned_data = super().clean()

        loanamount = self.cleaned_data["loanamount"]
        weight = self.cleaned_data["weight"]
        purity = self.cleaned_data["purity"]
        itemtype = self.cleaned_data["itemtype"]
        rate = (
            Rate.objects.filter(metal=itemtype).latest("timestamp").buying_rate
            if Rate.objects.filter(metal=itemtype).exists()
            else 0
        )
        value = round(weight * purity * Decimal(0.01) * rate)

        if value < loanamount:
            raise forms.ValidationError(
                f"Loan amount {loanamount} cannot exceed items value {value}."
            )

        return cleaned_data


class ReleaseForm(forms.ModelForm):
    created = forms.DateTimeField(
        input_formats=["%d/%m/%Y %H:%M"],
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local",
                "data-date-format": "DD MMMM YYYY",
                "max": datetime.now(),
            }
        ),
    )
    loan = forms.ModelChoiceField(widget=LoansWidget, queryset=Loan.unreleased.all())

    class Meta:
        model = Release
        fields = [
            "releaseid",
            "loan",
            "interestpaid",
        ]

    def clean_created(self):
        cleaned_data = super().clean()
        my_date = cleaned_data.get("created")

        if my_date and my_date > timezone.now():
            raise forms.ValidationError("Date cannot be in the future.")

        return my_date

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column("releaseid", css_class="form-group col-md-4 mb-0"),
                Column("created", css_class="form-group col-md-4 mb-0"),
                css_class="form-row",
            ),
            Row(
                Column("loan", css_class="form-group col-md-4 mb-0"),
                Column("interestpaid", css_class="form-group col-md-4 mb-0"),
                css_class="form-row",
            ),
            Submit("submit", "Submit"),
        )


class BulkReleaseForm(forms.Form):
    date = forms.DateTimeField(
        input_formats=["%d/%m/%Y %H:%M"],
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local",
                "data-date-format": "DD MMMM YYYY",
            }
        ),
    )
    loans = forms.ModelMultipleChoiceField(
        widget=MultipleLoansWidget, queryset=Loan.unreleased.all()
    )


class StatementItemForm(forms.ModelForm):
    loan = forms.ModelMultipleChoiceField(
        widget=MultipleLoansWidget,
        queryset=Loan.objects.unreleased().filter(series__is_active=True),
    )

    class Meta:
        model = StatementItem
        fields = "__all__"


class AdjustmentForm(forms.ModelForm):
    created = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local",
                "data-date-format": "DD MMMM YYYY",
            }
        )
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
