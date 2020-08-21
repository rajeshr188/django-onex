from django import forms
from django.forms import modelformset_factory
from django.forms.models import inlineformset_factory
from .models import Approval,ApprovalLine,ApprovalLineReturn,ApprovalReturn,ApprovalReturnLine
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

    def save(self,commit = True):

        approvalline = super(ApprovalLineForm,self).save(commit = False)
        if approvalline.id:

            if any( x in self.changed_data for x in ['product','quantity','weight']):
                ApprovalLine.objects.get(id = approvalline.id).delete()
            
        if commit:
            approvalline.save()
        return approvalline

class ApprovalReturnForm(forms.ModelForm):
    class Meta:
        model = ApprovalReturn
        fields = ['approval']

class ApprovalReturnLineForm(forms.ModelForm):
    product = forms.ModelChoiceField(queryset = Stree.objects.filter(children__isnull = True,).exclude(barcode = ''))
    class Meta:
        model = ApprovalReturnLine
        fields = ['product','quantity','weight']

Approval_formset = inlineformset_factory(Approval,ApprovalLine,
                    fields = ('approval','product','quantity','weight','touch','returned_wt','returned_qty'),
                    form = ApprovalLineForm,
                    extra=1,can_delete=True)
approvallinereturn_formset = modelformset_factory(ApprovalLineReturn,fields=('line','quantity','weight'))
ApprovalReturn_formset = inlineformset_factory(ApprovalReturn,ApprovalReturnLine,
                    fields = ('approvalreturn','product','quantity','weight'),
                    form = ApprovalReturnLineForm,
                    extra = 1,can_delete = True)
