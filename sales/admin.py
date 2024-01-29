import decimal

from django import forms
from django.contrib import admin

from contact.models import Customer

from .models import Invoice, InvoiceItem, Receipt

# from import_export import fields, resources
# from import_export.admin import (ImportExportActionModelAdmin,
#                                  ImportExportModelAdmin)
# from import_export.widgets import DecimalWidget, ForeignKeyWidget


# class CustomDecimalWidget(DecimalWidget):
#     """
#     Widget for converting decimal fields.
#     """

#     def clean(self, value, row=None):
#         if self.is_empty(value):
#             return None
#         return decimal.Decimal(str(value))


# class customerWidget(ForeignKeyWidget):
#     def clean(self, value, row=None, *args, **kwargs):
#         return self.model.objects.get_or_create(name=value, type="Wh")[0]


class InvoiceAdminForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = "__all__"


# class InvoiceResource(resources.ModelResource):
#     # customer = fields.Field(column_name='customer',attribute='customer',
#     #                         widget=ForeignKeyWidget(Customer,'name'))
#     customer = fields.Field(
#         column_name="customer",
#         attribute="customer",
#         widget=customerWidget(Customer, "name"),
#     )

#     class Meta:
#         model = Invoice
#         fields = (
#             "id",
#             "customer",
#             "created",
#             "is_ratecut",
#             "status",
#         )
#         skip_unchanged = True
#         report_skipped = False


# class InvoiceAdmin(ImportExportActionModelAdmin):
class InvoiceAdmin(admin.ModelAdmin):
    form = InvoiceAdminForm
    # resource_class = InvoiceResource
    list_display = [
        "id",
        "created_at",
        "customer",
        "updated_at",
        "is_ratecut",
        "status",
    ]


admin.site.register(Invoice, InvoiceAdmin)


class InvoiceItemAdminForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = "__all__"


class InvoiceItemAdmin(admin.ModelAdmin):
    form = InvoiceItemAdminForm
    list_display = ["weight", "touch", "is_return", "quantity"]


admin.site.register(InvoiceItem, InvoiceItemAdmin)


class ReceiptAdminForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = "__all__"


# class ReceiptResource(resources.ModelResource):
#     customer = fields.Field(
#         column_name="customer",
#         attribute="customer",
#         widget=ForeignKeyWidget(Customer, "name"),
#     )
#     total = fields.Field(
#         column_name="total", attribute="total", widget=CustomDecimalWidget()
#     )

#     class Meta:
#         model = Receipt
#         fields = (
#             "id",
#             "customer",
#             "created",
#             "updated",
#             "total",
#             "description",
#             "status",
#         )
#         skip_unchanged = True
#         report_skipped = False


# class ReceiptAdmin(ImportExportActionModelAdmin):
class ReceiptAdmin(admin.ModelAdmin):
    form = ReceiptAdminForm
    # resource_class = ReceiptResource
    list_display = [
        "id",
        "customer",
        "created_at",
        "updated_at",
        "total",
        "description",
        "status",
    ]


admin.site.register(Receipt, ReceiptAdmin)
