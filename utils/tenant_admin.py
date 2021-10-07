from django.contrib import admin
from django.conf import settings
from django.contrib.admin.forms import AuthenticationForm

class TenantAwareAdminSite(admin.AdminSite):
    
    # to allow non-staff users to login to admin
    login_form = AuthenticationForm
    def has_permission(self, request):
        """
        Checks if the current user has access.
        """
        return request.user.is_active

    def get_app_list(self,request):
        """override to return only the apps that are appropriate tenant-aware/public"""
        # check if current schema is public
        is_public = request.tenant.name == 'public'
    
        app_list = super(TenantAwareAdminSite,self).get_app_list(request)
        tenant_aware_apps = []
        for app in app_list:
            if is_public:
                if app["app_label"] in settings.SHARED_APPS:    
                    tenant_aware_apps.append(app)
            else:
                if app["app_label"] in settings.TENANT_APPS:   
                    tenant_aware_apps.append(app)
        
        return tenant_aware_apps

admin_site = TenantAwareAdminSite(name="tenant-admin")
