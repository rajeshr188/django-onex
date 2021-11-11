from django import forms
from django.forms import modelformset_factory,inlineformset_factory
from .models import Approval,ApprovalLine,ApprovalLineReturn
from product.models import Stock
from contact.models import Customer
from django_select2.forms import Select2Widget

class ApprovalForm(forms.ModelForm):
    contact= forms.ModelChoiceField(queryset = Customer.objects.all(),widget = Select2Widget)
    class Meta:
        model = Approval
        fields = ['contact']

class ApprovalLineForm(forms.ModelForm):
    product = forms.ModelChoiceField(
                queryset = Stock.objects.filter(status = 'Available'),
                widget = Select2Widget)
    class Meta:
        model = ApprovalLine
        fields = ['product','quantity','weight','touch']

Approval_formset = inlineformset_factory(Approval,ApprovalLine,
                    fields = ('approval','product','quantity','weight','touch'),
                    form = ApprovalLineForm,extra=2,can_delete=True)

approvallinereturn_formset = modelformset_factory(ApprovalLineReturn,fields=('line','quantity','weight'))
