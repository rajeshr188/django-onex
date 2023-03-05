from django import forms

from sea.models import drs


class drsForm(forms.Form):
    class Meta:
        model = drs
        fields = "__all__"
