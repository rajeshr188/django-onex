from django import forms
from django.urls import reverse_lazy
from .models import Customer
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from django_select2 import forms as s2forms

class CustomerWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "name__icontains",
        "relatedas__icontains",
        "relatedto__icontains",
        "phonenumber__icontains",
    ]
    
class CustomerForm(forms.ModelForm):
    Address = forms.CharField(widget=forms.Textarea({'rows': 3}),
                              help_text='address..')
                              
    class Meta:
        model = Customer
        fields = ['type','name','pic','relatedas','relatedto','phonenumber','Address', 'area']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.attrs = {
            'hx-boost': 'true',
            'hx-target': '#customer-content',
            'hx-swap': 'innerHTML',
            'hx-push-url':'true',
        }
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-3 mb-0'),
                Column('relatedas', css_class='form-group col-md-3 mb-0'),
                Column('relatedto', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('type', css_class='form-group col-md-3 mb-0'),
                Column('pic', css_class='form-group col-md-3 mb-0'),
                Column('phonenumber', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
           
            Row(
                Column('Address', css_class='form-group col-md-3 mb-0'),
                Column('area', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            
            Submit('submit', 'Submit')
        )
