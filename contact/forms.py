from django import forms
from django_select2 import forms as s2forms

from .models import Address, Contact, Customer, Proof


class CustomerWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "name__icontains",
        "relatedas__icontains",
        "relatedto__icontains",
        "contactno__phone_number__icontains",
    ]


class CustomerForm(forms.ModelForm):
    Address = forms.CharField(widget=forms.Textarea({"rows": 3}), help_text="address..")

    class Meta:
        model = Customer
        fields = [
            "customer_type",
            "name",
            "pic",
            "relatedas",
            "relatedto",
            "Address",
            "area",
        ]


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            "area",
            "doorno",
            "zipcode",
            "street",
            # "Customer",
        ]

    # def __init__(self, *args, **kwargs):
    #     super(AddressForm, self).__init__(*args, **kwargs)
    #     self.fields["Customer"].queryset = Customer.objects.all()


class ContactForm(forms.ModelForm):
    # phone_number = PhoneNumberField(region="IN")

    class Meta:
        model = Contact
        fields = [
            "contact_type",
            "phone_number",
            # "customer",
        ]

    # def __init__(self, *args, **kwargs):
    #     super(ContactForm, self).__init__(*args, **kwargs)
    #     self.fields["Customer"].queryset = Customer.objects.all()


class ProofForm(forms.ModelForm):
    class Meta:
        model = Proof
        fields = [
            "proof_type",
            "proof_no",
            "doc",
            "Customer",
        ]

    def __init__(self, *args, **kwargs):
        super(ProofForm, self).__init__(*args, **kwargs)
        self.fields["Customer"].queryset = Customer.objects.all()


class CustomerMergeForm(forms.Form):
    original = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        widget=CustomerWidget(
            select2_options={
                "width": "100%",
            }
        ),
    )
    duplicate = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        widget=CustomerWidget(
            select2_options={
                "width": "100%",
            }
        ),
    )
