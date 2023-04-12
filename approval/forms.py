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

    def clean_weight(self):
        weight = self.cleaned_data["weight"]
        if weight < 0:
            raise forms.ValidationError("Weight cannot be negative")
        return weight
    
    def clean_quantity(self):
        qty = self.cleaned_data['quantity']
        if qty < 0:
            raise forms.ValidationError("Quantity cannot be negative")
        return qty

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        weight = cleaned_data.get("weight")
        quantity = cleaned_data.get("quantity")
        stock_bal = product.current_balance()
        if weight > stock_bal['wt']  or quantity > stock_bal['qty']:
            raise forms.ValidationError("Weight or quantity cannot be greater than stock balance")
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

    def clean_weight(self):
        weight = self.cleaned_data["weight"] 
        if weight < 0 :
            raise forms.ValidationError("Weight cannot be negative")
        return weight
    
    def clean_quantity(self):
        errors = {}
        qty = self.cleaned_data['quantity']
        if qty < 0:
            raise forms.ValidationError("Quantity cannot be negative")
        return qty

    def clean(self):
        cleaned_data = super().clean()
        line = cleaned_data['line_item']
        qty = cleaned_data['quantity']
        wt = cleaned_data['weight']
        if qty > line.quantity or weight > line.weight:
            raise forms.ValidationError("weight or quanitity is returned in excess")
        
        return cleaned_data
