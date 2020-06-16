from django.shortcuts import render
from django.views.generic import ListView,CreateView,DetailView,UpdateView,DeleteView
from .models import Approval,ApprovalLine,ApprovalReturn,ApprovalReturnLine
from.forms import (ApprovalForm,ApprovalLineForm,ApprovalReturnForm,
                ApprovalReturnLineForm,Approval_formset,ApprovalReturn_formset)
from django.urls import reverse,reverse_lazy
from django.http import HttpResponseRedirect,HttpResponse
from product.models import Stree
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
            self.object.total_qty +=i.quantity
            self.object.total_wt +=i.weight
            self.object.save()

            approval_node = Stree.objects.get(name='Approval')

            if i.product.tracking_type == 'Lot':
                i.product.weight -= i.weight
                i.product.quantity -=i.quantity
                i.product.save()
                i.product.update_status()
                approval_node = approval_node.traverse_parellel_to(i.product)
                approval_node.weight += i.weight
                approval_node.quantity +=i.quantity
                approval_node.save()
            else:
                approval_node = approval_node.traverse_parellel_to(i.product,include_self=False)
                i.product.move_to(approval_node,position='first-child')
                i.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self,form,approvalline_form):
        return self.render_to_response(self.get_context_data(
            form=form,approvalline_form=approvalline_form))


class ApprovalDetailView(LoginRequiredMixin,DetailView):
    model = Approval

class ApprovalUpdateView(LoginRequiredMixin,UpdateView):
    model = Approval
    form_class = ApprovalForm

    def get(self,request,*args,**kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        approvalline_form = Approval_formset(instance=self.object)

        return self.render_to_response(self.get_context_data(form = form,
                                        approvalline_form = approvalline_form))

    def post(self,request,*args,**kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        approvalline_form = Approval_formset(self.request.POST,instance=self.object)

        if (form.is_valid() and approvalline_form.is_valid()):
            return self.form_valid(form,approvalline_form)
        else:
            return self.form_invalid(form,approvalline_form)

    def form_valid(self,form,approvalline_form):
        self.object = form.save()
        ApprovalLine.objects.filter(approval=self.object).delete()
        approvalline_form.instance = self.object
        items = approvalline_form.save()
        for i in items:
            self.object.total_qty +=i.quantity
            self.object.total_wt +=i.weight
            self.object.save()

            approval_node = Stree.objects.get(name='Approval')

            if i.product.tracking_type == 'Lot':
                i.product.weight -= i.weight
                i.product.quantity -=i.quantity
                i.product.save()
                i.product.update_status()
                approval_node = approval_node.traverse_parellel_to(i.product)
                approval_node.weight += i.weight
                approval_node.quantity +=i.quantity
                approval_node.save()
            else:
                approval_node = approval_node.traverse_parellel_to(i.product,include_self=False)
                i.product.move_to(approval_node,position='first-child')

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self,form,approvalline_form):
        return self.render_to_response(self.get_context_data(
            form=form,approvalline_form=approvalline_form))


class ApprovalDeleteView(LoginRequiredMixin,DeleteView):
    model = Approval
    success_url = reverse_lazy('approval_approval_list')

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
