from django import forms
from .models import Customer
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['type','name','pic','relatedas','relatedto','phonenumber','Address', 'area']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
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
