from django import forms
from django_select2 import forms as s2forms

from product.models import PricingTier

from .models import Address, Contact, Customer, Proof


class CustomerWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "name__icontains",
        "relatedas__icontains",
        "relatedto__icontains",
        "contactno__phone_number__icontains",
    ]


class CustomerForm(forms.ModelForm):
    pricing_tier = forms.ModelChoiceField(queryset=PricingTier.objects.all())
    name = forms.CharField(
        max_length=255,
        #  forms ↓
        widget=forms.TextInput(attrs={"autofocus": True}),
    )

    class Meta:
        model = Customer
        fields = [
            "customer_type",
            "name",
            "pic",
            "relatedas",
            "relatedto",
            "pricing_tier",
        ]


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            "doorno",
            "street",
            "area",
            "zipcode",
        ]
        widgets = {
            "street": forms.Textarea(attrs={"rows": 3}),
            "doorno": forms.TextInput(attrs={"autofocus": True}),
        }

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
