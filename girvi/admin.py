from django.contrib import admin
from django import forms
from import_export import fields,resources
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from .models import License, Loan, Release, Series, Adjustment
from contact.models import Customer
from utils.tenant_admin import admin_site

class LicenseAdminForm(forms.ModelForm):

    class Meta:
        model = License
        fields = '__all__'


class LicenseAdmin(admin.ModelAdmin):
    form = LicenseAdminForm
    list_display = ['name', 'id', 'created', 'updated', 'type', 'shopname', 'address', 'phonenumber', 'propreitor']

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request) -> bool:
        return True

admin_site.register(License, LicenseAdmin)
admin_site.register(Series)
admin_site.register(Adjustment)

class LoanResource(resources.ModelResource):
    customer = fields.Field(column_name='customer',
                            attribute='customer',
                            widget=ForeignKeyWidget(Customer,'pk'))
    # license=fields.Field(column_name='license',
    #                         attribute='license',
    #                         widget=ForeignKeyWidget(License,'id'))
    series = fields.Field(column_name='series',
                            attribute='series',
                            widget=ForeignKeyWidget(Series,'id'))
    class Meta:
        model=Loan
        #import_id_fields = ('id',)
        fields=('id','loanid','customer','series','created','itemtype','itemweight','itemdesc','loanamount','interestrate','value')

class LoanAdminForm(forms.ModelForm):
    date_heirarchy = 'created'
    list_filter = ('customer','series','itemtype')
    class Meta:
        model = Loan
        fields = '__all__'

class LoanAdmin(ImportExportModelAdmin):
    form = LoanAdminForm
    resource_class=LoanResource
    list_display = ['id','loanid','customer','series','created', 'updated', 'itemtype', 'itemdesc', 'itemweight', 'itemvalue', 'loanamount', 'interestrate', 'interest']

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request) -> bool:
        return True

admin_site.register(Loan, LoanAdmin)

class ReleaseResource(resources.ModelResource):

    loan=fields.Field(column_name='loan',
                            attribute='loan',
                            widget=ForeignKeyWidget(Loan,'pk'))
    class Meta:
        model=Release
        fields=('releaseid','created','loan','interestpaid')

class ReleaseAdminForm(forms.ModelForm):

    class Meta:
        model = Release
        fields = '__all__'

class ReleaseAdmin(ImportExportModelAdmin):
    form = ReleaseAdminForm
    resource_class=ReleaseResource

    list_display = ['releaseid','loan','created', 'updated', 'interestpaid']

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request) -> bool:
        return True

admin_site.register(Release, ReleaseAdmin)
