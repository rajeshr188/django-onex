from sea.models import Transaction,Account,Statement,drs
from django.contrib import admin
from django import forms
from import_export import fields,resources
from import_export.admin import ImportExportModelAdmin, ImportExportActionModelAdmin
from import_export.widgets import ForeignKeyWidget

# Register your models here.

class AccountAdmin(admin.ModelAdmin):
    list_display = ['name']

class TransactionResource(resources.ModelResource):
    account = fields.Field(column_name='account',
                            attribute='account',
                            widget=ForeignKeyWidget(Account, 'name'))
    class Meta:
        model = Transaction
        fields = ['id','account','date','txn_type','amount']

class TransactionAdminForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = '__all__'

class TransactionAdmin(ImportExportActionModelAdmin):
    form = TransactionAdminForm
    resource_class = TransactionResource
    list_display = ['id','account','date','txn_type','amount']

class drsAdminForm(forms.ModelForm):
    class Meta:
        model =drs
        fields = '__all__'
class drsAdmin(admin.ModelAdmin):
    form = drsAdminForm
    list_display = ['period','account','cb']

admin.site.register(Account,AccountAdmin)
admin.site.register(Transaction,TransactionAdmin)
admin.site.register(drs,drsAdmin)