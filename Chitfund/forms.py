from django import forms
from .models import Contact, Chit, Collection, Allotment
from django.forms.widgets import CheckboxSelectMultiple
from datetime import datetime
from django.utils import timezone
from django_select2.forms import Select2MultipleWidget
class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'phoneno']

class ChitForm(forms.ModelForm):
    members=forms.ModelMultipleChoiceField(
        widget=Select2MultipleWidget,
        queryset=Contact.objects.all())
    class Meta:
        model = Chit
        fields = ['name', 'type', 'amount', 'commission', 'member_limit', 'date_to_allot', 'owner', 'members']

    def clean(self):
        m=self.cleaned_data['members']
        if len(m)>self.cleaned_data['member_limit']:
            raise forms.ValidationError("Only {} members are ALlowed to be added".format(self.cleaned_data['member_limit']))


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['allotment', 'member','amount', ]

    def clean(self):
        a=self.cleaned_data['allotment']
        m=self.cleaned_data['member']

        if Collection.objects.filter(member=m,allotment=a).exists():
            # member_chitcount=a.chit.members.filter(id=member.id).count()
            # if Collection.objects.filter(member=m,allotment=a).count() >=member_chitcount
            #     raise forms.ValidationError("Already Paid")
            raise forms.ValidationError("Already Paid")


class AllotmentForm(forms.ModelForm):
    class Meta:
        model = Allotment
        fields = ['created','chit','amount', 'to_member',]

    def clean(self):
        c=self.cleaned_data['created']
        m=self.cleaned_data['to_member']
        if Allotment.objects.filter(to_member=m).exists():
            raise forms.ValidationError("{} has already been allotted".format(m))
        if Allotment.objects.filter(created__month__gte=c.month,created__year__gte=c.year).exists():
            raise forms.ValidationError("Only One ALlotment Per Month Sorry!\n Chit for {} th month is alloted".format(c.month))
