import decimal

from django import forms
from django.contrib import admin
from import_export import fields, resources
from import_export.admin import (ImportExportActionModelAdmin,
                                 ImportExportModelAdmin)
from import_export.widgets import DecimalWidget, ForeignKeyWidget

from contact.models import Customer

from .models import Invoice, InvoiceItem, Payment


class CustomDecimalWidget(DecimalWidget):
    """
    Widget for converting decimal fields.
    """

    def clean(self, value, row=None):
        if self.is_empty(value):
            return None
        return decimal.Decimal(str(value))


class supplierWidget(ForeignKeyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        return self.model.objects.get_or_create(name=value, type="Wh")[0]


class InvoiceAdminForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = "__all__"


class InvoiceResource(resources.ModelResource):
    supplier = fields.Field(
        column_name="supplier",
        attribute="supplier",
        widget=supplierWidget(Customer, "name"),
    )

    class Meta:
        model = Invoice
        fields = (
            "id",
            "supplier",
            "created",
            "rate",
            "balancetype",
            "balance",
            "status",
        )
        skip_unchanged = True
        report_skipped = False


class InvoiceAdmin(ImportExportActionModelAdmin):
    form = InvoiceAdminForm
    resource_class = InvoiceResource
    list_display = [
        "id",
        "created",
        "updated",
        "rate",
        "balancetype",
        "balance",
        "status",
    ]


admin.site.register(Invoice, InvoiceAdmin)


class InvoiceItemAdminForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = "__all__"


class InvoiceItemAdmin(admin.ModelAdmin):
    form = InvoiceItemAdminForm
    list_display = ["weight", "touch", "total", "is_return", "quantity"]


admin.site.register(InvoiceItem, InvoiceItemAdmin)


class PaymentAdminForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = "__all__"


class PaymentResourse(resources.ModelResource):
    supplier = fields.Field(
        column_name="supplier",
        attribute="supplier",
        widget=ForeignKeyWidget(Customer, "name"),
    )
    total = fields.Field(
        column_name="total", attribute="total", widget=CustomDecimalWidget()
    )

    class Meta:
        model = Payment
        skip_unchanged = True
        report_skipped = False


class PaymentAdmin(ImportExportActionModelAdmin):
    form = PaymentAdminForm
    resource_class = PaymentResourse
    list_display = [
        "id",
        "created",
        "updated",
        "type",
        "total",
        "description",
        "status",
    ]


admin.site.register(Payment, PaymentAdmin)
