from django import forms
from django.forms import modelformset_factory,inlineformset_factory,BaseInlineFormSet
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

# class CustomInlineFormSet(BaseInlineFormSet):
#     def clean(self):
#         super().clean()

#         if any(self.errors):
#             print("didnt bother validating")
#         # Don't bother validating the formset unless each form is valid on its own
#             return
#         products = {}
#         for form in self.forms:

#             if self.can_delete and self._should_delete_form(form):
#                 continue
#             print(f" form.cleaned_data: {form.cleaned_data} ")
#             product = form.cleaned_data.get('product')
#             if product:
#                 if product.id in products:
#                     products[product.id]['qty'] +=form.cleaned_data['quantity']
#                     products[product.id]['wt'] += form.cleaned_data['weight']

#                 else:
#                     products[product.id]={'product':product,
#                                         # "qty":form.cleaned_data['quantity'],
#                                         "wt":form.cleaned_data['weight']}
#         print(f"\n{len(products)}product evaluated for validation {products}")

#         for line in products:
#             print(f"line: {products[line]['product']} qty : {products[line]['qty']} wt: {products[line]['wt']}")
#             p = products[line]['product']
#             q = products[line]['qty']
#             w = products[line]['wt']
#             if p.quantity < q or p.weight < w:
#                 # raise ValidationError("Articles in a set must have distinct titles.")
#                 print(f"{p.quantity} < {q} or {p.weight} < {w} evaluation failed")
#             else:
#                 print("evaluation passed")
#         print("\n exiting formset clean()")

# class ApprovalReturnForm(forms.ModelForm):
#     class Meta:
#         model = ApprovalReturn
#         fields = ['approval']
#
# class ApprovalReturnLineForm(forms.ModelForm):
#     product = forms.ModelChoiceField(queryset = Stree.objects.filter(children__isnull = True,).exclude(barcode = ''))
#     class Meta:
#         model = ApprovalReturnLine
#         fields = ['product','quantity','weight']

Approval_formset = inlineformset_factory(Approval,ApprovalLine,
                    fields = ('approval','product','quantity','weight','touch'),
                    form = ApprovalLineForm,
                    # formset=CustomInlineFormSet,
                    extra=1,can_delete=True)

approvallinereturn_formset = modelformset_factory(ApprovalLineReturn,fields=('line','quantity','weight'))

# ApprovalReturn_formset = inlineformset_factory(ApprovalReturn,ApprovalReturnLine,
#                     fields = ('approvalreturn','product','quantity','weight'),
#                     form = ApprovalReturnLineForm,
#                     extra = 1,can_delete = True)
