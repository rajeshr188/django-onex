from django.contrib import admin
from .models import PaymentTerm
from utils.tenant_admin import admin_site
# Register your models here.
class PaymentTermAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request) -> bool:
        return True
admin_site.register(PaymentTerm,PaymentTermAdmin)