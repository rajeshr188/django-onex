from django import forms
from django_select2.forms import Select2Widget

from contact.forms import CustomerWidget
from contact.models import Customer
from product.models import StockLot
from django.db.models import Sum
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


    def clean_weight(self):
        weight = self.cleaned_data["weight"]
        if weight < 0:
            raise forms.ValidationError("Weight cannot be negative")
        return weight

    def clean_quantity(self):
        qty = self.cleaned_data["quantity"]
        if qty < 0:
            raise forms.ValidationError("Quantity cannot be negative")
        return qty

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        weight = cleaned_data.get("weight")
        quantity = cleaned_data.get("quantity")
        stock_bal = product.current_balance()
        if weight > stock_bal["wt"] or quantity > stock_bal["qty"]:
            raise forms.ValidationError(
                "Weight or quantity cannot be greater than stock balance"
            )
        return cleaned_data


class ReturnForm(forms.ModelForm):
    contact = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        # widget=Select2Widget
        widget=CustomerWidget,
    )

    class Meta:
        model = Return
        fields = ["contact"]


class ReturnItemForm(forms.ModelForm):
    line_item = forms.ModelChoiceField(
        queryset=ApprovalLine.objects.all(),
        widget=Select2Widget,
    )

    class Meta:
        model = ReturnItem
        fields = ["line_item", "quantity", "weight"]
    
    def __init__(self,*args, **kwargs):
        return_obj = kwargs.pop('return_obj', None)
        super().__init__(*args, **kwargs)
        if return_obj:
            # self.fields['line_item'].queryset = StockLot.objects.filter(
            #     # below filter can be usefull if we want to return only items that are not returned
            #     # but we have scenarios where we want to return items that are already partially returned
            #     approval_lineitems__approval__contact=return_instance.contact,  # Filter by contact
            #     returnline__isnull=True,  # Only products without a return line
            # )
            return_instance = Return.objects.get(pk=return_obj.pk)
            qs = ApprovalLine.objects.exclude(
                        status='Returned'
                        ).filter(approval__contact=return_instance.contact,  # Filter by contact
                        # return_items__isnull=True,  # Only products without a return line
                        )
                    # .values_list("product", flat=True)
            print(f"line_item_qs:{qs}")
            self.fields['line_item'].queryset = qs

    def clean_weight(self):
        weight = self.cleaned_data["weight"]
        if weight < 0:
            raise forms.ValidationError("Weight cannot be negative")
        return weight

    def clean_quantity(self):
        errors = {}
        qty = self.cleaned_data["quantity"]
        if qty < 0:
            raise forms.ValidationError("Quantity cannot be negative")
        return qty
    def clean_line_item(self):
        line = self.cleaned_data["line_item"]
        if not line:
            raise forms.ValidationError("Item is required")
        if line.status == 'Returned':
            raise forms.ValidationError("This item is already returned")
        return line
    def clean(self):
        cleaned_data = super().clean()
        line = cleaned_data["line_item"]
        if not line:
            raise forms.ValidationError("Item is required")
        qty = cleaned_data["quantity"]
        wt = cleaned_data["weight"]
        already_returned = line.return_items.aggregate(qty = Sum('quantity'), wt = Sum('weight'))
        if qty > line.quantity or wt > line.weight:
            raise forms.ValidationError("weight or quanitity is returned in excess")

        return cleaned_data
