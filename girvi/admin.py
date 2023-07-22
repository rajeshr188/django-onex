from django import forms
from django.contrib import admin

# from import_export import fields, resources
# from import_export.admin import ImportExportModelAdmin
# from import_export.widgets import ForeignKeyWidget

from contact.models import Customer

from .forms import LoanForm
from .models import Adjustment, License, Loan, Release, Series


class LicenseAdminForm(forms.ModelForm):
    class Meta:
        model = License
        fields = "__all__"


class LicenseAdmin(admin.ModelAdmin):
    form = LicenseAdminForm
    list_display = [
        "name",
        "id",
        "created",
        "updated",
        "type",
        "shopname",
        "address",
        "phonenumber",
        "propreitor",
    ]


admin.site.register(License, LicenseAdmin)
admin.site.register(Series)
admin.site.register(Adjustment)


# class LoanResource(resources.ModelResource):
#     customer = fields.Field(
#         column_name="customer",
#         attribute="customer",
#         widget=ForeignKeyWidget(Customer, "pk"),
#     )
#     # license=fields.Field(column_name='license',
#     #                         attribute='license',
#     #                         widget=ForeignKeyWidget(License,'id'))
#     series = fields.Field(
#         column_name="series", attribute="series", widget=ForeignKeyWidget(Series, "id")
#     )

#     class Meta:
#         model = Loan
#         # import_id_fields = ('id',)
#         fields = (
#             "id",
#             "loanid",
#             "customer",
#             "series",
#             "created",
#             "itemtype",
#             "itemweight",
#             "itemdesc",
#             "loanamount",
#             "interestrate",
#             "value",
#         )


class LoanAdminForm(forms.ModelForm):
    date_heirarchy = "created"
    list_filter = ("customer", "series", "itemtype")

    class Meta:
        model = Loan
        fields = "__all__"


# class LoanAdmin(ImportExportModelAdmin):
class LoanAdmin(admin.ModelAdmin):
    form = LoanAdminForm
    # resource_class = LoanResource
    list_display = [
        "id",
        "loanid",
        "customer",
        "series",
        "created",
        "updated",
        "itemtype",
        "itemdesc",
        "itemweight",
        "itemvalue",
        "loanamount",
        "interestrate",
    ]
    search_fields = ["customer__name", "series"]
    autocomplete_fields = ["customer"]


admin.site.register(Loan, LoanAdmin)


# class ReleaseResource(resources.ModelResource):
#     loan = fields.Field(
#         column_name="loan", attribute="loan", widget=ForeignKeyWidget(Loan, "pk")
#     )

#     class Meta:
#         model = Release
#         fields = ("releaseid", "created", "loan", "interestpaid")


class ReleaseAdminForm(forms.ModelForm):
    class Meta:
        model = Release
        fields = "__all__"


# class ReleaseAdmin(ImportExportModelAdmin):
class ReleaseAdmin(admin.ModelAdmin):
    form = ReleaseAdminForm
    # resource_class = ReleaseResource

    list_display = ["releaseid", "loan", "created", "updated", "interestpaid"]


admin.site.register(Release, ReleaseAdmin)
