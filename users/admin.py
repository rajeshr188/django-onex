from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from utils.tenant_admin import admin_site
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['email', 'username',]

    def has_add_permission(self, request):
        return request.user.is_superuser and request.tenant.name == 'public'

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and request.tenant.name == 'public'

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser and request.tenant.name == 'public'

admin_site.register(CustomUser, CustomUserAdmin)
