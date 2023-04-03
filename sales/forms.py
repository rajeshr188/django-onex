from crispy_forms.helper import FormHelper
from crispy_forms.layout import (ButtonHolder, Column, Field, Layout, Row,
                                 Submit)
from django import forms
from django.forms.models import inlineformset_factory
from django_select2.forms import Select2Widget
from django_tables2 import Column

from approval.models import Approval
from contact.models import Customer
from product.forms import StockWidget
from product.models import StockLot
from utils.custom_layout_object import *

from .models import Invoice, InvoiceItem, Receipt, ReceiptItem, ReceiptLine
from django.urls import reverse_lazy

class DateTimeLocalInput(forms.DateTimeInput):
    input_type = "datetime-local"


class DateTimeLocalField(forms.DateTimeField):
    # Set DATETIME_INPUT_FORMATS here because, if USE_L10N
    # is True, the locale-dictated format will be applied
    # instead of settings.DATETIME_INPUT_FORMATS.
    # See also:
    # https://developer.mozilla.org/en-US/docs/Web/HTML/Date_and_time_formats

    input_formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M"]
    widget = DateTimeLocalInput(format="%Y-%m-%dT%H:%M")


class InvoiceForm(forms.ModelForm):
    created = DateTimeLocalField()
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(), widget=Select2Widget
    )
    approval = forms.ModelChoiceField(
        queryset=Approval.objects.filter(status="Pending"),
        widget=Select2Widget,
        required=False,
    )

    class Meta:
        model = Invoice
        fields = [
            "created",
            "approval",
            "rate",
            "is_gst",
            "balancetype",
            "metaltype",
            "term",
            "customer",
        ]

    def __init__(self, *args, **kwargs):
        super(InvoiceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        # self.helper.form_show_labels = False
        self.helper.form_tag = False
        self.helper.form_class = "form-group"
        self.helper.label_class = "col-md-6 form-label"
        self.helper.field_class = "col-md-12"

        self.helper.layout = Layout(
            Row(
                Column(Field("created", css_class="form-control ")),
                Column(Field("customer", css_class="form-control ")),
                css_class="form-row",
            ),
            Row(
                Column(Field("balancetype", css_class="form-control ")),
                Column(Field("metaltype", css_class="form-control ")),
                Column(Field("rate", css_class="form-control ")),
                css_class="form-row",
            ),
            Row(
                Column(Field("approval", css_class="form-control")),
                Column(Field("term", css_class="form-control ")),
                css_class="form-row",
            ),
            Field("is_gst"),
            ButtonHolder(Submit("submit", "save")),
        )


class InvoiceItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=StockLot.objects.all(),
        widget=StockWidget,
    )

    class Meta:
        model = InvoiceItem
        fields = [
            "is_return",
            "product",
            "quantity",
            "weight",
            "less_stone",
            "net_wt",
            "touch",
            "wastage",
            "makingcharge",
            "total",
        ]
        widgets = {
            'weight': forms.NumberInput(
                attrs={
                    "hx-include":"[name='customer'], [name='product']",
                    "hx-get": reverse_lazy("sales:sale_product_price"),
                    "hx-target": "#div_id_touch",
                    "hx-trigger": "change",
                    "hx-swap": "innerHTML",
                }
            )
        }


class ReceiptForm(forms.ModelForm):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(customer_type="Wh"), widget=Select2Widget
    )
    created = DateTimeLocalInput()

    class Meta:
        model = Receipt
        fields = [
            "created",
            "customer",
            "type",
            "rate",
            "total",
            "description",
            "status",
        ]


class ReceiptLineForm(forms.ModelForm):
    invoice = forms.ModelChoiceField(
        queryset=Invoice.objects.all(), widget=Select2Widget
    )

    class Meta:
        model = ReceiptLine
        fields = ["invoice", "amount"]


ReceiptLineFormSet = inlineformset_factory(
    Receipt,
    ReceiptLine,
    fields=("invoice", "amount", "receipt"),
    extra=0,
    can_delete=True,
    form=ReceiptLineForm,
)


class ReceiptItemForm(forms.ModelForm):
    class Meta:
        models = ReceiptItem
        fields = "__all__"


ReceiptItemFormSet = inlineformset_factory(
    Receipt,
    ReceiptItem,
    fields=("weight", "touch", "nettwt", "amount", "receipt"),
    extra=1,
    can_delete=True,
    form=ReceiptItemForm,
)
