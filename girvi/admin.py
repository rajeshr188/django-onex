from django.contrib import admin
from django import forms
from import_export import fields,resources
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from .models import License, Loan, Release, Series, Adjustment
from contact.models import Customer

class LicenseAdminForm(forms.ModelForm):

    class Meta:
        model = License
        fields = '__all__'


class LicenseAdmin(admin.ModelAdmin):
    form = LicenseAdminForm
    list_display = ['name', 'id', 'created', 'last_updated', 'type', 'shopname', 'address', 'phonenumber', 'propreitor']

admin.site.register(License, LicenseAdmin)
admin.site.register(Series)
admin.site.register(Adjustment)

class LoanResource(resources.ModelResource):
    customer=fields.Field(column_name='customer',
                            attribute='customer',
                            widget=ForeignKeyWidget(Customer,'pk'))
    license=fields.Field(column_name='license',
                            attribute='license',
                            widget=ForeignKeyWidget(License,'id'))
    class Meta:
        model=Loan
        #import_id_fields = ('id',)
        fields=('id','loanid','customer','license','series','created','itemtype','itemweight','itemdesc','loanamount','interestrate','value')

class LoanAdminForm(forms.ModelForm):

    class Meta:
        model = Loan
        fields = '__all__'


class LoanAdmin(ImportExportModelAdmin):
    form = LoanAdminForm
    resource_class=LoanResource
    list_display = ['id','loanid','license','series','created', 'last_updated', 'itemtype', 'itemdesc', 'itemweight', 'itemvalue', 'loanamount', 'interestrate', 'interest']

admin.site.register(Loan, LoanAdmin)

class ReleaseResource(resources.ModelResource):
    # customer=fields.Field(column_name='customer',
    #                         attribute='customer',
    #                         widget=ForeignKeyWidget(Customer,'pk'))
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

    list_display = ['releaseid','loan','created', 'last_updated', 'interestpaid']

admin.site.register(Release, ReleaseAdmin)
