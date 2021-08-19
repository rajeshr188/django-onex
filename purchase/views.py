from decimal import Context
from dea.models import AccountStatement
from django.http.response import Http404
from django.views.generic import DetailView, ListView, UpdateView, CreateView,DeleteView
from django.db.models import Sum, Q, F, OuterRef, Subquery
from django.shortcuts import render, redirect
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy

from .models import Invoice, InvoiceItem, Payment,PaymentLine
from .tables import InvoiceTable,PaymentTable
from .forms import (InvoiceForm, InvoiceItemForm, 
                    InvoiceItemFormSet, PaymentForm,
                    PaymentItemFormSet, PaymentLineForm,
                    )
from .filters import InvoiceFilter, PaymentFilter
from .render import Render

from contact.models import Customer
from num2words import num2words

from django_tables2.views import SingleTableMixin
from django_tables2.export.views import ExportMixin
from django_filters.views import FilterView

def home(request):
    context = {}
    qs = Invoice.objects
    qs_posted = qs.posted()
    
    total = dict()
    total['total']=qs_posted.total_with_ratecut()
    if total['total']['cash']:
        total['total']['gmap'] = round(total['total']['cash_g'] / \
            total['total']['cash_g_nwt'],3)
        total['total']['smap'] = round(total['total']['cash_s'] / \
            total['total']['cash_s_nwt'],3)
    else:
        total['total']['gmap']=0
        total['total']['smap'] = 0
    
    total['gst'] = qs_posted.gst().total_with_ratecut()
    if total['gst']['cash']: 
        total['gst']['gmap'] = round(total['gst']['cash_g']/total['gst']['cash_g_nwt'],3)
        total['gst']['smap'] = round(total['gst']['cash_s']/total['gst']['cash_s_nwt'],3)
    else:
        total['gst']['gmap']=0
        total['gst']['smap']=0
    
    total['nongst'] = qs_posted.non_gst().total_with_ratecut()
    if total['nongst']['cash']:
        total['nongst']['gmap'] = round(total['nongst']['cash_g']/total['nongst']['cash_g_nwt'],3)
        total['nongst']['smap'] = round(total['nongst']['cash_s']/total['nongst']['cash_s_nwt'],3)
    else:
        total['nongst']['gmap']=0
        total['nongst']['smap']=0
   
    context['total'] = total
    
    return render(request,'purchase/home.html',context)

def print_invoice(pk):
    invoice=Invoice.objects.get(id=pk)
    params={'invoice':invoice}
    return Render.render('purchase/invoice_pdf.html',params)

def print_payment(pk):
    payment=Payment.objects.get(id=pk)
    params={'payment':payment,'inwords':num2words(payment.total,lang='en_IN')}
    return Render.render('purchase/payment.html',params)

# def home(request):
#     data={}
#     data['qs']=Invoice.objects.all()
#     return render(request,'purchase/home.html',context = {'data':data})

def list_balance(request):
    acs = AccountStatement.objects.filter(AccountNo__contact = OuterRef('supplier')).order_by('-created')[:1]
    acs_cb = AccountStatement.objects.filter(
        AccountNo__contact=OuterRef('pk')).order_by('-created')[:1]
    payments=Payment.objects.filter(
        posted = True,
        supplier=OuterRef('pk'),
        created__gte = Subquery(acs.values('created'))
        ).order_by().values('supplier')
    grec=payments.annotate(grec=Sum('total',filter=Q(type='Gold'))).values('grec')
    crec=payments.annotate(crec=Sum('total',filter=Q(type='Cash'))).values('crec')
    invoices = Invoice.objects.posted().filter(
        supplier=OuterRef('pk'),
        created__gte=Subquery(acs.values('created'))
        ).order_by().values('supplier')
    gbal=invoices.annotate(gbal=Sum('balance',filter=Q(balancetype='Gold'))).values('gbal')
    cbal=invoices.annotate(cbal=Sum('balance',filter=Q(balancetype='Cash'))).values('cbal')

    balance=Customer.objects.filter(type="Su").annotate(
                                    cb = Subquery(acs_cb.values('ClosingBalance')),
                                    gbal=Subquery(gbal),grec=Subquery(grec),gold=F('gbal')-F('grec')
                                    ,cbal=Subquery(cbal),crec=Subquery(crec),cash=F('cbal')-F('crec'))
    context={'balance':balance}
    return render(request,'purchase/balance_list.html',context)

class InvoiceListView(ExportMixin,SingleTableMixin,FilterView):
    model = Invoice
    table_class = InvoiceTable
    filterset_class = InvoiceFilter
    template_name = 'purchase/invoice_list.html'
    paginate_by = 25

class InvoiceCreateView(CreateView):
    model = Invoice
    form_class = InvoiceForm

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        invoiceitem_form = InvoiceItemFormSet()

        return self.render_to_response(
            self.get_context_data(form=form,
                                  invoiceitem_form=invoiceitem_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        invoiceitem_form = InvoiceItemFormSet(self.request.POST)

        if (form.is_valid() and invoiceitem_form.is_valid()):
            return self.form_valid(form, invoiceitem_form)
        else:
            return self.form_invalid(form, invoiceitem_form)

    def form_valid(self, form, invoiceitem_form):
        if invoiceitem_form.is_valid():
            self.object = form.save()
            invoiceitem_form.instance = self.object
            invoiceitem_form.save()
            self.object.gross_wt = self.object.get_gross_wt()
            self.object.net_wt = self.object.get_net_wt()
            self.object.balance = self.object.get_total_balance()
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, invoiceitem_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(
            self.get_context_data(form=form,
                                  invoiceitem_form=invoiceitem_form))

class InvoiceDetailView(DetailView):
    model = Invoice

    def get_context_data(self, **kwargs):
        context = super(InvoiceDetailView, self).get_context_data(**kwargs)
        context['previous'] = self.object.get_previous()
        context['next'] = self.object.get_next()
        return context

class InvoiceUpdateView(UpdateView):
    model = Invoice
    form_class = InvoiceForm

    def get_context_data(self,*args,**kwargs):
        data = super(InvoiceUpdateView,self).get_context_data(**kwargs)
        if self.object.posted:
            raise Http404
        if self.request.POST:
            data['invoiceitem_form'] = InvoiceItemFormSet(self.request.POST,
                                                    instance = self.object)
        else:
            data['invoiceitem_form'] = InvoiceItemFormSet(instance = self.object)
        return data

    @transaction.atomic()
    def form_valid(self, form):
        context = self.get_context_data()
        invoiceitem_form = context['invoiceitem_form']

        print(f"form_valid:{invoiceitem_form.is_valid()}")
        if invoiceitem_form.is_valid():
            self.object = form.save()
            invoiceitem_form.save()
            self.object.gross_wt = self.object.get_gross_wt()
            self.object.net_wt = self.object.get_net_wt()
            self.object.balance = self.object.get_total_balance()
            self.object.save()
           
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, invoiceitem_form):
        return self.render_to_response(
            self.get_context_data(form=form,
                                  invoiceitem_form=invoiceitem_form))

def post_purchase(request,pk):
    # use get_objector404
    purchase_inv = Invoice.objects.get(id = pk)
    # post to dea & stock
    purchase_inv.post()
    return redirect(purchase_inv)

def unpost_purchase(request,pk):
    purchase_inv = Invoice.objects.get(id = pk)
    # unpost to dea & stock
    purchase_inv.unpost() 
    return redirect(purchase_inv)

class InvoiceDeleteView(DeleteView):
    model = Invoice
    success_url = reverse_lazy('purchase_invoice_list')

class InvoiceItemListView(ListView):
    model = InvoiceItem

class InvoiceItemCreateView(CreateView):
    model = InvoiceItem
    form_class = InvoiceItemForm

class InvoiceItemDetailView(DetailView):
    model = InvoiceItem

class InvoiceItemUpdateView(UpdateView):
    model = InvoiceItem
    form_class = InvoiceItemForm

class PaymentListView(ExportMixin,SingleTableMixin,FilterView):
    model = Payment
    table_class = PaymentTable
    filterset_class = PaymentFilter
    template_name="purchase/payment_list.html"
    paginate_by = 25

class PaymentCreateView(CreateView):
    model = Payment
    form_class = PaymentForm

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        paymentitem_form = PaymentItemFormSet()

        return self.render_to_response(
            self.get_context_data(form=form,
                                  paymentitem_form=paymentitem_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        paymentitem_form = PaymentItemFormSet(self.request.POST)
        if (form.is_valid() and paymentitem_form.is_valid()):
            return self.form_valid(form, paymentitem_form)
        else:
            return self.form_invalid(form, paymentitem_form)

    def form_valid(self, form, paymentitem_form):
        self.object = form.save()
        paymentitem_form.instance = self.object
        paymentitem_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, paymentitem_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(
            self.get_context_data(form=form,
                                  paymentitem_form=paymentitem_form))

class PaymentDetailView(DetailView):
    model = Payment

class PaymentUpdateView(UpdateView):
    model = Payment
    form_class = PaymentForm

class PaymentDeleteView(DeleteView):
    model = Payment
    success_url = reverse_lazy('purchase_payment_list')

class PaymentLineCreateView(CreateView):
    model = PaymentLine
    form_class = PaymentLineForm

class PaymentLineDeleteView(DeleteView):
    model = PaymentLine
    success_url = reverse_lazy('purchase_paymentline_list')

def post_payment(request,pk):
    # use get_objector404
    payment = Payment.objects.get(id = pk)
    # post to dea
    payment.post()
    return redirect(payment)

def unpost_payment(request,pk):
    payment = Payment.objects.get(id = pk)
    # unpost to dea
    payment.unpost()
    return redirect(payment)
