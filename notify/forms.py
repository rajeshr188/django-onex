from django import forms
from .models import NoticeGroup

class NoticeGroupForm(forms.ModelForm):
    class Meta:
        model = NoticeGroup
        fields = '__all__'