from django import forms
from .models import Customer, Supplier


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['type','name','pic','relatedas','relatedto','phonenumber','Address', 'area']


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name','pic', 'organisation', 'phonenumber', 'initial']
