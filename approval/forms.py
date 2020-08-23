from django import forms
from django.forms import modelformset_factory,inlineformset_factory,BaseInlineFormSet
# from django.forms.models import inlineformset_factory
from .models import Approval,ApprovalLine,ApprovalLineReturn,ApprovalReturn,ApprovalReturnLine
from product.models import Stree
from contact.models import Customer
from django_select2.forms import Select2Widget,ModelSelect2Widget
from mptt.forms import TreeNodeChoiceField
from django.core.exceptions import ValidationError

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
        print("In form save")
        approvalline = super(ApprovalLineForm,self).save(commit = False)
        if approvalline.id:

            if any( x in self.changed_data for x in ['product','quantity','weight']):

                old_data = ApprovalLine.objects.get(id = approvalline.id)
                if approvalline.product.tracking_type == 'Lot':

                    approval_node = Stree.objects.get(name='Approval')
                    approval_node = approval_node.traverse_parellel_to(approvalline.product)
                    approval_node.transfer(approvalline.product,old_data.quantity,old_data.weight)
                else:
                    stock = Stree.objects.get(name='Stock')
                    stock = stock.traverse_parellel_to(approvalline.product,include_self=False)
                    approvalline.product.move_to(stock,position='first-child')

        if commit:
            try:
                approvalline.save()
            except Exception:
                raise Exception("up you go")
        return approvalline

class CustomInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        if any(self.errors):
            print("didnt bother validating")
        # Don't bother validating the formset unless each form is valid on its own
            return
        products = {}
        for form in self.forms:

            if self.can_delete and self._should_delete_form(form):
                continue
            print(f" form.cleaned_data: {form.cleaned_data} ")
            product = form.cleaned_data.get('product')
            if product:
                if product.id in products:
                    products[product.id]['qty'] +=form.cleaned_data['quantity']
                    products[product.id]['wt'] += form.cleaned_data['weight']

                else:
                    products[product.id]={'product':product,
                                        "qty":form.cleaned_data['quantity'],
                                        "wt":form.cleaned_data['weight']}
        print(f"\n{len(products)}product evaluated for validation {products}")

        for line in products:
            print(f"line: {products[line]['product']} qty : {products[line]['qty']} wt: {products[line]['wt']}")
            p = products[line]['product']
            q = products[line]['qty']
            w = products[line]['wt']
            if p.quantity < q or p.weight < w:
                # raise ValidationError("Articles in a set must have distinct titles.")
                print(f"{p.quantity} < {q} or {p.weight} < {w} evaluation failed")
            else:
                print("evaluation passed")
        print("\nexiting formset clean()")

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
                    # formset=CustomInlineFormSet,
                    extra=1,can_delete=True)

approvallinereturn_formset = modelformset_factory(ApprovalLineReturn,fields=('line','quantity','weight'))

ApprovalReturn_formset = inlineformset_factory(ApprovalReturn,ApprovalReturnLine,
                    fields = ('approvalreturn','product','quantity','weight'),
                    form = ApprovalReturnLineForm,
                    extra = 1,can_delete = True)
