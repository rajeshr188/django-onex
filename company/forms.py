from django import forms
from .models import Company, Membership, Workspace
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name','address','state','pincode','mobileno']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-3 mb-0'),
                Column('mobileno', css_class='form-group col-md-3 mb-0'),
            ),
            Row(
                Column('address', css_class='form-group col-md-3 mb-0'),
                Column('state', css_class='form-group col-md-3 mb-0'),
                Column('pincode', css_class='form-group col-md-3 mb-0'),
            ),
            Submit('submit','Submit')
        )

class WorkspaceForm(forms.ModelForm):

    def __init__(self,user,*args, **kwargs):
        super(WorkspaceForm, self).__init__(*args, **kwargs)
        
        self.fields['company'].queryset = user.company_set.all()
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('company', css_class='form-group col-md-3 mb-0')),
            Submit('submit','Submit')
        )

    class Meta:
        model = Workspace
        fields = ['company','user']

class MembershipForm(forms.ModelForm):
    def __init__(self,user,*args,**kwargs):
        super(MembershipForm,self).__init__(*args,**kwargs)

        self.fields['company'].queryset = user.company_set.all()
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('company', css_class='form-group col-md-3 mb-0'),
                Column('user', css_class='form-group col-md-3 mb-0'),
                Column('role', css_class='form-group col-md-3 mb-0'),


                ),
            Submit('submit', 'Submit')
        )

    def clean(self):
        cleaned_data = super().clean()
        company = cleaned_data.get("company")
        user = cleaned_data.get("user")

        if Membership.objects.filter(user=user,company = company).exists():
            msg = "this user is already a member of this company"
            self.add_error('user', msg)

    class Meta:
        model = Membership
        fields ='__all__'

    

