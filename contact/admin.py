from django import forms
from django.contrib import admin
from import_export import fields, resources
from import_export.admin import ImportExportActionModelAdmin, ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget

from .models import Customer, Contact, Address, Proof


class CustomerResource(resources.ModelResource):
    class Meta:
        model = Customer


class CustomerAdminForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = "__all__"


class CustomerAdmin(ImportExportActionModelAdmin):
    form = CustomerAdminForm
    resource_class = CustomerResource
    search_fields = ["name", "relatedto", "Address"]
    list_display = [
        "name",
        "id",
        "created",
        "updated",
        "Address",
        "area",
        "customer_type",
        "relatedas",
        "relatedto",
    ]
    readonly_fields = [
        "name",
        "id",
        "created",
        "updated",
        "Address",
        "area",
        "customer_type",
        "relatedas",
        "relatedto",
    ]


class AddressAdminForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = "__all__"


class AddressAdmin(admin.ModelAdmin):
    form = AddressAdminForm
    list_display = [
        "area",
        "created",
        "doorno",
        "zipcode",
        "last_updated",
        "street",
    ]
    readonly_fields = [
        "area",
        "created",
        "doorno",
        "zipcode",
        "last_updated",
        "street",
    ]


class ContactAdminForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = "__all__"


class ContactAdmin(admin.ModelAdmin):
    form = ContactAdminForm
    list_display = [
        "created",
        "contact_type",
        "phone_number",
        "last_updated",
    ]
    readonly_fields = [
        "created",
        "contact_type",
        "phone_number",
        "last_updated",
    ]


class ProofAdminForm(forms.ModelForm):
    class Meta:
        model = Proof
        fields = "__all__"


class ProofAdmin(admin.ModelAdmin):
    form = ProofAdminForm
    list_display = [
        "proof_type",
        "created",
        "proof_no",
        "doc",
        "last_updated",
    ]
    readonly_fields = [
        "proof_type",
        "created",
        "proof_no",
        "doc",
        "last_updated",
    ]


admin.site.register(Customer, CustomerAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(Proof, ProofAdmin)
