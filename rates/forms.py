from django import forms
from .models import Rate, RateSource

class RateForm(forms.ModelForm):
    class Meta:
        model = Rate
        fields = '__all__'  # You can specify the fields you want to include instead of '__all__'

class RateSourceForm(forms.ModelForm):
    class Meta:
        model = RateSource
        fields = '__all__'  # You can specify the fields you want to include instead of '__all__'
