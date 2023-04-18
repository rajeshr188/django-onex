from datetime import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import (ButtonHolder, Column, Field, Fieldset, Layout,
                                 Row, Submit)
from django import forms
from django.db.models import Q
from django.urls import reverse_lazy
from django_select2.forms import Select2Widget

from contact.models import Customer
from product.models import ProductVariant
from utils.custom_layout_object import *

from .models import Invoice, InvoiceItem, Payment, PaymentAllocation


class InvoiceForm(forms.ModelForm):
    supplier = forms.ModelChoiceField(
        queryset=Customer.objects.exclude(customer_type="Re"), widget=Select2Widget
    )
    created = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                "class": "form-control datetimepicker-input",
                "type": "datetime-local",
            }
        )
    )
    # pull in rate from rate model
    # rate = forms.NumberInput(
    #     attrs={
    #         "class": "form-control"
    #     })

    class Meta:
        model = Invoice
        fields = [
            "created",
            "rate",
            "is_gst",
            "balancetype",
            "metaltype",
            "gross_wt",
            "net_wt",
            "total",
            "balance",
            "supplier",
            "term",
            "status",
        ]

    def __init__(self, *args, **kwargs):
        super(InvoiceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = "form-group"
        self.helper.label_class = "col-md-6 create-label"
        self.helper.field_class = "col-md-12"
        self.helper.layout = Layout(
            Row(
                Column(
                    Field("created", css_class="form-control"),
                    css_class="form-group col-md-3 mb-0",
                ),
                Column(
                    Field("supplier", css_class="form-control"),
                    css_class="form-group col-md-3 mb-0",
                ),
                Column(Field("is_gst"), css_class="form-group col-md-3 mb-0"),
                css_class="form-row",
            ),
            Row(
                Column("balancetype", css_class="form-group col-md-3 mb-0"),
                Column("metaltype", css_class="form-group col-md-3 mb-0"),
                Column("rate", css_class="form-group col-md-3 mb-0"),
                css_class="form-row",
            ),
            Fieldset("Add items", Formset("items")),
            Row(
                Column(
                    Field("gross_wt", css_class="form-control"),
                    css_class="form-group col-md-3 mb-0",
                ),
                Column(
                    Field("net_wt", css_class="form-control"),
                    css_class="form-group col-md-3 mb-0",
                ),
                Column(
                    Field("total", css_class="form-control"),
                    css_class="form-group col-md-3 mb-0",
                ),
                css_class="form-row",
            ),
            Row(
                Column("term", css_class="form-group col-md-3 mb-0"),
                Column("balance", css_class="form-group col-md-3 mb-0"),
                Column("status", css_class="form-group col-md-3 mb-0"),
                css_class="form-row",
            ),
            ButtonHolder(Submit("submit", "save")),
        )


class InvoiceUpdateForm(InvoiceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout.fields[-1].value = "Save Changes"


class InvoiceItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=ProductVariant.objects.all(), widget=Select2Widget
    )

    class Meta:
        model = InvoiceItem
        fields = [
            "is_return",
            "product",
            "weight",
            "touch",
            # "total",
            "quantity",
            # "invoice",
            "makingcharge",
            # "net_wt",
        ]
        widgets = {
            "weight": forms.NumberInput(
                attrs={
                    "hx-include": "[name='supplier'], [name='product']",
                    "hx-get": reverse_lazy("purchase:price_history"),
                    "hx-target": "#div_id_touch",
                    "hx-trigger": "change",
                    "hx-swap": "innerHTML",
                }
            )
        }

    def save(self, commit=True):
        instance = super(InvoiceItemForm, self).save(commit=False)
        instance.total = self.cleaned_data["weight"] * self.cleaned_data["touch"]
        if commit:
            instance.save()
        return instance


class PaymentForm(forms.ModelForm):
    created = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    contact = forms.ModelChoiceField(
        queryset=Customer.objects.filter(customer_type="S"), widget=Select2Widget
    )

    class Meta:
        model = Payment
        fields = [
            "supplier",
            "created",
            "payment_type",
            "rate",
            "total",
            "description",
            "status",
        ]
