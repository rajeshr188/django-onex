from crispy_bootstrap5.bootstrap5 import FloatingField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit
from django import forms
from django.urls import reverse_lazy, reverse
from django_select2 import forms as s2forms
from django_select2.forms import ModelSelect2Widget, Select2Widget
from .models import Customer, Contact, Address, Proof
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget


class CustomerWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "name__icontains",
        "relatedas__icontains",
        "relatedto__icontains",
        "contactno__number__icontains",
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

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.helper = FormHelper()

    #     self.helper.attrs = {
    #         # "hx-post":".",
    #         # "hx-select":'#customer-content',
    #         # "hx-target":'#customer-content',
    #         # "hx-swap":"innerHTML",

    #     }
    #     self.helper.layout = Layout(
    #         Row(
    #             Column(FloatingField("name"), css_class="form-group col-md-3 mb-0"),
    #             Column(
    #                 FloatingField("relatedas"), css_class="form-group col-md-3 mb-0"
    #             ),
    #             Column(
    #                 FloatingField("relatedto"), css_class="form-group col-md-3 mb-0"
    #             ),
    #             css_class="form-row",
    #         ),
    #         Row(
    #             Column(FloatingField("type"), css_class="form-group col-md-3 mb-0"),
    #             Column(FloatingField("pic"), css_class="form-group col-md-3 mb-0"),
    #             Column(
    #                 FloatingField("phonenumber"), css_class="form-group col-md-3 mb-0"
    #             ),
    #             css_class="form-row",
    #         ),
    #         Row(
    #             Column(FloatingField("Address"), css_class="form-group col-md-3 mb-0"),
    #             Column(FloatingField("area"), css_class="form-group col-md-3 mb-0"),
    #             css_class="form-row",
    #         ),
    #         Submit("submit", "Submit"),
    #     )


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
    phone_number = PhoneNumberField(region="IN")

    class Meta:
        model = Contact
        fields = [
            "contact_type",
            # "Customer",
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
        queryset=Customer.objects.all(), widget=CustomerWidget()
    )
    duplicate = forms.ModelChoiceField(
        queryset=Customer.objects.all(), widget=CustomerWidget()
    )

    class Meta:
        widgets = {"original": CustomerWidget, "duplicate": CustomerWidget}
