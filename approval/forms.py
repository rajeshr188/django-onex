from django import forms
from django.forms import inlineformset_factory, modelformset_factory
from django_select2.forms import Select2Widget

from contact.forms import CustomerWidget
from contact.models import Customer
from product.models import StockLot

from .models import Approval, ApprovalLine, ApprovalLineReturn


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
        queryset=StockLot.objects.filter(status="Available"), widget=Select2Widget
    )

    class Meta:
        model = ApprovalLine
        fields = ["product", "quantity", "weight", "touch"]


Approval_formset = inlineformset_factory(
    Approval,
    ApprovalLine,
    fields=("approval", "product", "quantity", "weight", "touch"),
    form=ApprovalLineForm,
    extra=1,
    can_delete=True,
)

approvallinereturn_formset = modelformset_factory(
    ApprovalLineReturn, fields=("line", "quantity", "weight")
)
