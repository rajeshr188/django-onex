from django import forms
from django_select2.forms import Select2Widget

from contact.forms import CustomerWidget
from contact.models import Customer
from product.models import StockLot

from .models import Approval, ApprovalLine, Return, ReturnItem


class ApprovalForm(forms.ModelForm):
    contact = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        # widget=Select2Widget
        widget=CustomerWidget,
    )

    class Meta:
        model = Approval
        fields = ["contact"]


class ApprovalLineForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        # change filter to available
        queryset=StockLot.objects.all(),
        widget=Select2Widget,
    )

    class Meta:
        model = ApprovalLine
        fields = ["product", "quantity", "weight", "touch"]


class ReturnForm(forms.ModelForm):
    contact = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        # widget=Select2Widget
        widget=CustomerWidget,
    )

    class Meta:
        model = Return
        fields = "__all__"


class ReturnItemForm(forms.ModelForm):
    line_item = forms.ModelChoiceField(
        queryset=ApprovalLine.objects.all(),
        widget=Select2Widget,
    )

    class Meta:
        model = ReturnItem
        fields = "__all__"
