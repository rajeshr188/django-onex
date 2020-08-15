from django.shortcuts import render
from django.views.generic import ListView,CreateView,DetailView,UpdateView,DeleteView
from .models import Approval,ApprovalLine,ApprovalReturn,ApprovalReturnLine
from.forms import (ApprovalForm,ApprovalLineForm,ApprovalReturnForm,
                ApprovalReturnLineForm,Approval_formset,ApprovalReturn_formset)
from django.urls import reverse,reverse_lazy
from django.http import HttpResponseRedirect,HttpResponse
from product.models import Stree
from contact.models import Customer
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
# Create your views here.

class ApprovalListView(LoginRequiredMixin,ListView):
    model = Approval

class ApprovalCreateView(LoginRequiredMixin,CreateView):
    model = Approval
    form_class = ApprovalForm

    def get(self,request,*args,**kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        approvalline_form = Approval_formset()

        return self.render_to_response(self.get_context_data(form = form,
                                        approvalline_form = approvalline_form))

    def post(self,request,*args,**kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        approvalline_form = Approval_formset(self.request.POST)

        if (form.is_valid() and approvalline_form.is_valid()):
            return self.form_valid(form,approvalline_form)
        else:
            return self.form_invalid(form,approvalline_form)

    def form_valid(self,form,approvalline_form):
        self.object = form.save()
        approvalline_form.instance = self.object
        items = approvalline_form.save()
        for i in items:
            approval_node,created = Stree.objects.get_or_create(name='Approval')

            if i.product.tracking_type == 'Lot':
                approval_node = approval_node.traverse_parellel_to(i.product)
                i.product.transfer(approval_node,i.quantity,i.weight)
            else:
                approval_node = approval_node.traverse_parellel_to(i.product,include_self=False)
                i.product.move_to(approval_node,position='first-child')
            i.save()
        self.object.update_status()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self,form,approvalline_form):
        return self.render_to_response(self.get_context_data(
            form=form,approvalline_form=approvalline_form))


class ApprovalDetailView(LoginRequiredMixin,DetailView):
    model = Approval

class ApprovalUpdateView(LoginRequiredMixin,UpdateView):
    model = Approval
    form_class = ApprovalForm

    def get_context_data(self,**kwargs):
        data = super(ApprovalUpdateView,self).get_context_data(**kwargs)
        if self.request.POST:
            data['approvalline_form'] = Approval_formset(self.request.POST,instance = self.object)
        else :
            data['approvalline_form'] = Approval_formset(instance = self.object)
        return data

    def form_valid(self,form):
        context = self.get_context_data()
        approvalline_form = context['approvalline_form']
        self.object = form.save()

        if approvalline_form.is_valid():
            approvalline_form.instance = self.object
            # print(approvalline_form.has_changed())
            items = approvalline_form.save(commit = False)
            # deleting old data if changed i.e submitting stock
            for i in items:
                if i.id:
                    old_data = ApprovalLine.objects.get(pk=i.id)
                    approval_node,created = Stree.objects.get_or_create(name='Approval')
                    if old_data.product.tracking_type == 'Lot':
                        # print('transfering old data')
                        approval_node = approval_node.traverse_parellel_to(i.product)
                        approval_node.transfer(i.product,old_data.quantity,old_data.weight)

            items = approvalline_form.save(commit = True)
            for i in items:
                # create with new data
                approval_node,created = Stree.objects.get_or_create(name='Approval')
                if i.product.tracking_type == 'Lot':
                    # print('transferring any updates')
                    approval_node = approval_node.traverse_parellel_to(i.product)
                    i.product.transfer(approval_node,i.quantity,i.weight)

                else:
                    approval_node = approval_node.traverse_parellel_to(i.product,include_self=False)
                    i.product.move_to(approval_node,position='first-child')
                i.save()


        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self,form,approvalline_form):
        return self.render_to_response(self.get_context_data(
            form=form,approvalline_form=approvalline_form))


class ApprovalDeleteView(LoginRequiredMixin,DeleteView):
    model = Approval
    success_url = reverse_lazy('approval_approval_list')

from .filters import ApprovalLineFilter
from django.forms import modelformset_factory
from .models import ApprovalLineReturn

def ApprovalLineReturnView(request):

    approvalline_list = ApprovalLine.objects.filter(status = 'Pending')
    approvalline_filter = ApprovalLineFilter(request.GET, queryset=approvalline_list)

    approvallinereturn_formset = modelformset_factory(ApprovalLineReturn,
                                        fields = ('line','quantity','weight'),
                                        extra = approvalline_filter.qs.count(),
                                        max_num = approvalline_filter.qs.count(),
                                        )
    if request.method == 'POST':
        formset = approvallinereturn_formset(request.POST)
        if formset.is_valid():
            # do something with the formset.cleaned_data
            # submit lines approval node to stock
            # update lines return_qty & return weight & status
            for form in formset:
                if form.cleaned_data['line'].product.tracking_type == 'Lot':
                    approval_node,created = Stree.objects.get_or_create(name='Approval')
                    approval_node = approval_node.traverse_parellel_to(form.cleaned_data['line'].product)
                    approval_node.transfer(form.cleaned_data['line'].product,form.cleaned_data['quantity'],form.cleaned_data['weight'])
                else:
                    stock = Stree.objects.get(name='Stock')
                    stock = stock.traverse_parellel_to(form.cleaned_data['line'].product,include_self=False)
                    form.cleaned_data['line'].product.move_to(stock,position='first-child')


                if form.cleaned_data['line'].quantity == form.cleaned_data['quantity'] and form.cleaned_data['line'].weight == form.cleaned_data['weight']:
                    form.cleaned_data['line'].returned_qty = form.cleaned_data['quantity']
                    form.cleaned_data['line'].returned_wt = form.cleaned_data['weight']
                    form.cleaned_data['line'].status = 'Returned'
                    # form.cleaned_data['line'].save()
                result = form.save()
                result.line.save()
    elif request.method == 'GET':
        contact = request.GET.get('approval__contact',False)
        if contact:
            formset = approvallinereturn_formset(
            initial = approvalline_filter.qs.values('product','quantity','weight'),
            )

            for form in formset:
                form.fields['line'].queryset = ApprovalLine.objects.filter(status = 'Pending',approval__contact_id = contact)
        else:
            formset = approvallinereturn_formset(
                                queryset = ApprovalLineReturn.objects.none()
                                )


    return render(request,'approval/approvallinereturn.html',{
                                    'filter':approvalline_filter,
                                    'formset':formset
                                    })

class ApprovalLineReturnListView(LoginRequiredMixin,ListView):
    model = ApprovalLineReturn

class ApprovalLineReturnDeleteView(LoginRequiredMixin,DeleteView):
    model = ApprovalLineReturn
    success_url = reverse_lazy('approval_approvallinereturn_list')

class ApprovalLineCreateView(LoginRequiredMixin,CreateView):
    model = ApprovalLine
    form_class = ApprovalLineForm

class ApprovalReturnListView(LoginRequiredMixin,ListView):
    model = ApprovalReturn

class ApprovalReturnCreateView(LoginRequiredMixin,CreateView):
    model = ApprovalReturn
    form_class = ApprovalReturnForm

class ApprovalReturnDetailView(LoginRequiredMixin,DetailView):
    model = ApprovalReturn

class ApprovalReturnUpdateView(LoginRequiredMixin,UpdateView):
    model = ApprovalReturn
    form_class = ApprovalReturnForm

class ApprovalReturnDeleteView(LoginRequiredMixin,DeleteView):
    model = ApprovalReturn
    success_url = reverse_lazy('approval_approvalreturn_list')

class ApprovalReturnLineCreateView(LoginRequiredMixin,CreateView):
    model = ApprovalReturnLine
    form_class = ApprovalReturnLineForm
