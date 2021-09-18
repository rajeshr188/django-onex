from django.http.response import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView,CreateView,DetailView,UpdateView,DeleteView
from .models import (Approval,ApprovalLine,ApprovalLineReturn)
                   
from .forms import ApprovalForm,ApprovalLineForm,Approval_formset
from .filters import ApprovalLineFilter
from django.forms import modelformset_factory
from django.urls import reverse,reverse_lazy
from django.http import HttpResponseRedirect

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db import transaction
from datetime import datetime

# Create your views here.
@transaction.atomic
def post_approval(request,pk):
    approval = get_object_or_404(Approval,pk=pk)
    approval.post()
    return redirect(approval)

@transaction.atomic
def unpost_approval(request,pk):
    approval = get_object_or_404(Approval, pk=pk)
    approval.unpost()
    return redirect(approval)

@transaction.atomic
def post_approvallinereturn(request, pk):
    approval_lr = get_object_or_404(ApprovalLineReturn, pk=pk)
    approval_lr.post()
    return redirect(approval_lr.line.approval)

@transaction.atomic
def unpost_approvallinereturn(request, pk):
    approval_lr = get_object_or_404(ApprovalLineReturn, pk=pk)
    approval_lr.unpost()
    return redirect(approval_lr.line.approval)

from sales.models import Invoice as sinv,InvoiceItem as sinvitem
from invoice.models import PaymentTerm
@transaction.atomic()
def convert_sales(request,pk):
    # create sales invoice and invoice items from approval
    approval = get_object_or_404(Approval,pk=pk)
    term = PaymentTerm.objects.first()

    sale = sinv.objects.create(
        created = datetime.now(),
        customer = approval.contact,
        approval =approval,
        term=term)
    for item in approval.items.all():
        i = sinvitem.objects.create(invoice =sale,
                product = item.product,
                weight = item.weight,
                quantity = item.quantity,
                touch = item.touch,
                total=(item.weight*item.touch)/100)
        i.save()

    sale.gross_wt = sale.get_gross_wt()
    sale.net_wt = sale.get_net_wt()
    sale.balance = sale.get_balance()
    sale.save()
    approval.is_billed = True
    approval.save()
    return redirect(sale)

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

    @transaction.atomic()
    def form_valid(self,form,approvalline_form):
        form.instance.created_by = self.request.user
        self.object = form.save()
        approvalline_form.instance = self.object
        items = approvalline_form.save()
        qty =0
        wt =0
        for i in items:
            qty +=i.quantity
            wt +=i.weight
        self.object.total_wt = wt
        self.object.total_qty =qty
        self.object.save(update_fields = ['total_wt','total_qty'])   
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
        if self.object.posted:
                raise Http404
        if self.request.POST:
            data['approvalline_form'] = Approval_formset(self.request.POST,
                                            instance = self.object)
        else :
            data['approvalline_form'] = Approval_formset(instance = self.object)
        return data

    @transaction.atomic()
    def form_valid(self,form):
        print("form valid")
        context = self.get_context_data()
        approvalline_form = context['approvalline_form']
        self.object = form.save()
        items = approvalline_form.save()
        qty = 0
        wt = 0
        for i in items:
            qty += i.quantity
            wt += i.weight
        self.object.total_wt = wt
        self.object.total_qty = qty
        self.object.save(update_fields=['total_wt', 'total_qty'])
    
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self,form,approvalline_form):
        return self.render_to_response(self.get_context_data(
            form=form,approvalline_form=approvalline_form))

class ApprovalDeleteView(LoginRequiredMixin,DeleteView):
    model = Approval
    success_url = reverse_lazy('approval_approval_list')

def ApprovalLineReturnView(request):

    approvalline_list = ApprovalLine.objects.filter(status = 'Pending')
    approvalline_filter = ApprovalLineFilter(request.GET, queryset=approvalline_list)

    approvallinereturn_formset = modelformset_factory(ApprovalLineReturn,
                                        fields = ('line','quantity','weight'),
                                        extra = approvalline_filter.qs.count(),
                                        max_num = approvalline_filter.qs.count())
    if request.method == 'POST':
        formset = approvallinereturn_formset(request.POST)
        # stocktranx from approval to available
        for form in formset:
            result = form.save()
            if not result.posted:
                result.post()
                result.posted = True
                result.save(update_fields=['posted'])
               
    elif request.method == 'GET':
        contact = request.GET.get('approval__contact',False)
        if contact:
            formset = approvallinereturn_formset(
                        initial = approvalline_filter.qs.values(
                            'product','quantity','weight'))

            for form in formset:
                form.fields['line'].queryset = ApprovalLine.objects.filter(
                    status = 'Pending',
                    approval__contact_id = contact)
        else:
            formset = approvallinereturn_formset(
                                queryset = ApprovalLineReturn.objects.none())

    return render(request,'approval/approvallinereturn.html',{
                                    'filter':approvalline_filter,
                                    'formset':formset})

class ApprovalLineReturnListView(LoginRequiredMixin,ListView):
    model = ApprovalLineReturn

class ApprovalLineReturnDeleteView(LoginRequiredMixin,DeleteView):
    model = ApprovalLineReturn
    success_url = reverse_lazy('approval_approvallinereturn_list')

class ApprovalLineCreateView(LoginRequiredMixin,CreateView):
    model = ApprovalLine
    form_class = ApprovalLineForm