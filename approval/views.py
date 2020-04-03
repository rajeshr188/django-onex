from django.shortcuts import render
from django.views.generic import ListView,CreateView,DetailView,UpdateView,DeleteView
from .models import Approval,ApprovalLine,ApprovalReturn,ApprovalReturnLine
from.forms import (ApprovalForm,ApprovalLineForm,ApprovalReturnForm,
                ApprovalReturnLineForm,Approval_formset,ApprovalReturn_formset)
from django.urls import reverse,reverse_lazy
from django.http import HttpResponseRedirect,HttpResponse
# Create your views here.

class ApprovalListView(ListView):
    model = Approval

class ApprovalCreateView(CreateView):
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
            i.product.weight -= i.weight
            i.product.quantity -=i.quantity
            i.product.save()
            i.product.update_status('Approval')
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self,form,approvalline_form):
        return self.render_to_response(self.get_context_data(
            form=form,approvalline_form=approvalline_form))


class ApprovalDetailView(DetailView):
    model = Approval

class ApprovalUpdateView(UpdateView):
    model = Approval
    form_class = ApprovalForm

class ApprovalDeleteView(DeleteView):
    model = Approval
    success_url = reverse_lazy('approval_approval_list')

class ApprovalLineCreateView(CreateView):
    model = ApprovalLine
    form_class = ApprovalLineForm

class ApprovalReturnListView(ListView):
    model = ApprovalReturn

class ApprovalReturnCreateView(CreateView):
    model = ApprovalReturn
    form_class = ApprovalReturnForm

class ApprovalReturnDetailView(DetailView):
    model = ApprovalReturn

class ApprovalReturnUpdateView(UpdateView):
    model = ApprovalReturn
    form_class = ApprovalReturnForm

class ApprovalReturnDeleteView(DeleteView):
    model = ApprovalReturn
    success_url = reverse_lazy('approval_approvalreturn_list')

class ApprovalReturnLineCreateView(CreateView):
    model = ApprovalReturnLine
    form_class = ApprovalReturnLineForm
