from django import forms
from django.contrib.admin.widgets import AdminDateWidget

class daybookform(forms.Form):
    date = forms.DateField(widget=AdminDateWidget())
