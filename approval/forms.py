from django import forms
from django.forms.models import inlineformset_factory
from .models import Approval,ApprovalLine,ApprovalReturn,ApprovalReturnLine
from product.models import Stree
from contact.models import Customer
from django_select2.forms import Select2Widget,ModelSelect2Widget
from mptt.forms import TreeNodeChoiceField

class ApprovalForm(forms.ModelForm):
    contact= forms.ModelChoiceField(queryset = Customer.objects.all(),widget = Select2Widget)
    class Meta:
        model = Approval
        fields = ['contact']

class ApprovalLineForm(forms.ModelForm):
    product = forms.ModelChoiceField(
                            queryset = Stree.objects.filter(
                            children__isnull = True,
                            ).exclude(barcode = ''),
                            widget = Select2Widget)
    class Meta:
        model = ApprovalLine
        fields = ['product','quantity','weight','touch','returned_qty','returned_wt']


class ApprovalReturnForm(forms.ModelForm):
    class Meta:
        model = ApprovalReturn
        fields = ['approval']

class ApprovalReturnLineForm(forms.ModelForm):
    product = forms.ModelChoiceField(queryset = Stree.objects.filter(children__isnull = True,status = 'Available').exclude(barcode = ''))
    class Meta:
        model = ApprovalReturnLine
        fields = ['product','quantity','weight']

Approval_formset = inlineformset_factory(Approval,ApprovalLine,
                    fields = ('approval','product','quantity','weight','touch','returned_wt','returned_qty'),
                    form = ApprovalLineForm,
                    extra=1,can_delete=True)

ApprovalReturn_formset = inlineformset_factory(ApprovalReturn,ApprovalReturnLine,
                    fields = ('approvalreturn','product','quantity','weight'),
                    form = ApprovalReturnLineForm,
                    extra = 1,can_delete = True)
