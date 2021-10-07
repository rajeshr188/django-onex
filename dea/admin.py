from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from utils.tenant_admin import admin_site
# Register your models here.
from . import models

class TestPermissions(admin.ModelAdmin):
    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request) -> bool:
        return True

class LedgerAdmin(MPTTModelAdmin):
    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request) -> bool:
        return True
    
# Register your models here.
admin_site.register(models.Account,TestPermissions)
admin_site.register(models.AccountType,TestPermissions)
admin_site.register(models.EntityType,TestPermissions)
admin_site.register(models.Ledger,LedgerAdmin)
admin_site.register(models.TransactionType_DE, TestPermissions)
admin_site.register(models.TransactionType_Ext, TestPermissions)
admin_site.register(models.LedgerTransaction, TestPermissions)
admin_site.register(models.LedgerStatement, TestPermissions)
admin_site.register(models.AccountType_Ext, TestPermissions)
admin_site.register(models.AccountTransaction, TestPermissions)
admin_site.register(models.AccountStatement, TestPermissions)
admin_site.register(models.Journal, TestPermissions)
