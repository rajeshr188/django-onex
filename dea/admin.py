from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from mptt.models import MPTTModel

# Register your models here.
from . import models

class JournalAdmin(admin.ModelAdmin):
    list_display = ('id','content_type','content_object','created','updated','desc')
    list_filter = ('journal_type',)
    search_fields = ('voucher__id',)
# Register your models here.
admin.site.register(models.Account)
admin.site.register(models.AccountType)
admin.site.register(models.EntityType)
admin.site.register(models.Ledger, MPTTModelAdmin)
admin.site.register(models.TransactionType_DE)
admin.site.register(models.TransactionType_Ext)
admin.site.register(models.LedgerTransaction)
admin.site.register(models.LedgerStatement)
admin.site.register(models.AccountType_Ext)
admin.site.register(models.AccountTransaction)
admin.site.register(models.AccountStatement)
admin.site.register(models.Journal,JournalAdmin)
