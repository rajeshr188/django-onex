from django.contrib import admin
from django import forms
from .models import Contact, Chit, Collection, Allotment

class ContactAdminForm(forms.ModelForm):

    class Meta:
        model = Contact
        fields = '__all__'


class ContactAdmin(admin.ModelAdmin):
    form = ContactAdminForm
    list_display = ['name', 'slug', 'created', 'last_updated', 'phoneno']
    readonly_fields = ['name', 'slug', 'created', 'last_updated', 'phoneno']

admin.site.register(Contact, ContactAdmin)


class ChitAdminForm(forms.ModelForm):

    class Meta:
        model = Chit
        fields = '__all__'


class ChitAdmin(admin.ModelAdmin):
    form = ChitAdminForm
    list_display = ['name', 'slug', 'created', 'last_updated', 'type', 'amount', 'commission', 'member_limit', 'date_to_allot']
    readonly_fields = ['name', 'slug', 'created', 'last_updated', 'type', 'amount', 'commission', 'member_limit', 'date_to_allot']

admin.site.register(Chit, ChitAdmin)


class CollectionAdminForm(forms.ModelForm):

    class Meta:
        model = Collection
        fields = '__all__'


class CollectionAdmin(admin.ModelAdmin):
    form = CollectionAdminForm
    list_display = ['slug', 'date_collected', 'amount','allotment','member']
    readonly_fields = ['slug', 'date_collected', 'amount']

admin.site.register(Collection, CollectionAdmin)


class AllotmentAdminForm(forms.ModelForm):

    class Meta:
        model = Allotment
        fields = '__all__'


class AllotmentAdmin(admin.ModelAdmin):
    form = AllotmentAdminForm
    list_display = ['amount', 'slug', 'created','installment']
    readonly_fields = ['amount', 'slug', 'created','installment']

admin.site.register(Allotment, AllotmentAdmin)
