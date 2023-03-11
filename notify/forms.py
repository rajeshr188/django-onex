from django import forms
from .models import NoticeGroup, Notification


class NoticeGroupForm(forms.ModelForm):
    class Meta:
        model = NoticeGroup
        fields = "__all__"


class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = "__all__"
