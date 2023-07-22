from django import forms
from django.contrib import admin

# from import_export import fields, resources
# from import_export.admin import (ImportExportActionModelAdmin,
#                                  ImportExportModelAdmin)
# from import_export.widgets import ForeignKeyWidget

from sea.models import Account, Statement, Transaction, drs

# Register your models here.


class AccountAdmin(admin.ModelAdmin):
    list_display = ["name"]


# class TransactionResource(resources.ModelResource):
#     account = fields.Field(
#         column_name="account",
#         attribute="account",
#         widget=ForeignKeyWidget(Account, "name"),
#     )

#     class Meta:
#         model = Transaction
#         fields = ["id", "account", "date", "txn_type", "amount"]


class TransactionAdminForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = "__all__"


# class TransactionAdmin(ImportExportActionModelAdmin):
class TransactionAdmin(admin.ModelAdmin):
    form = TransactionAdminForm
    # resource_class = TransactionResource
    list_display = ["id", "account", "date", "txn_type", "amount"]


class drsAdminForm(forms.ModelForm):
    class Meta:
        model = drs
        fields = "__all__"


class drsAdmin(admin.ModelAdmin):
    form = drsAdminForm
    list_display = ["period", "account", "cb"]


admin.site.register(Account, AccountAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(drs, drsAdmin)
