from sea.models import drs
from django import forms

class drsForm(forms.Form):
    class Meta:
        model = drs
        fields = '__all__'