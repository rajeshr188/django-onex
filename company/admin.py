from django.contrib import admin

from utils.tenant_admin import admin_site
from .models import Company,CompanyOwner,Membership

class CompanyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return request.user.is_superuser and request.tenant.name == 'public'

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and request.tenant.name == 'public'

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser and request.tenant.name == 'public'

admin_site.register(Company,CompanyAdmin)
admin_site.register(CompanyOwner,CompanyAdmin)
admin_site.register(Membership,CompanyAdmin)