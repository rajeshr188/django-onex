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
from .forms import (InvoiceForm,InvoiceItemForm, 
                    InvoiceItemFormSet, InvoiceUpdateForm, PaymentForm,
                    PaymentItemFormSet, PaymentLineForm,
                    )
from .filters import InvoiceFilter, PaymentFilter
from .render import Render

from contact.models import Customer
from num2words import num2words

from django_tables2.views import SingleTableMixin
from django_tables2.export.views import ExportMixin
from django_filters.views import FilterView
import logging

logger = logging.getLogger(__name__)
def home(request):

    context = {}
    qs = Invoice.objects
    qs_posted = qs.posted()
    
    total = dict()
    total['total']=qs_posted.total_with_ratecut()
    total['gst'] = qs_posted.gst().total_with_ratecut()
    total['nongst'] = qs_posted.non_gst().total_with_ratecut()
    logger.warning(total)
    for i in total:
        if total[i]['cash']:
            if total[i]['cash_g']:
                total[i]['gmap'] = round(total[i]['cash_g'] /
                                            total[i]['cash_g_nwt'], 3)
            else:
                total[i]['gmap'] = 0
            if total[i]['cash_s']:
                total[i]['smap'] = round(total[i]['cash_s'] /
                                            total[i]['cash_s_nwt'], 3)
            else:
                total[i]['smap'] = 0
   
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
    
def list_balance(request):
    acs = AccountStatement.objects.filter(
                    AccountNo__contact = OuterRef('supplier')
                    ).order_by('-created')[:1]
    acs_cb = AccountStatement.objects.filter(
                    AccountNo__contact=OuterRef('pk')
                    ).order_by('-created')[:1]
    
    payments = Payment.objects.filter(
                posted = True,
                supplier=OuterRef('pk'),
                created__gte = Subquery(acs.values('created'))
                ).order_by().values('supplier')
    grec=payments.annotate(
                grec=Sum('total',filter=Q(type='USD'))
                ).values('grec')
    crec=payments.annotate(
                crec=Sum('total',filter=Q(type='INR'))
                ).values('crec')

    invoices = Invoice.objects.posted().filter(
                supplier=OuterRef('pk'),
                created__gte=Subquery(acs.values('created'))
                ).order_by().values('supplier')
    gbal=invoices.annotate(
                gbal=Sum('balance',filter=Q(balancetype='USD'))
                ).values('gbal')
    cbal=invoices.annotate(
                cbal=Sum('balance',filter=Q(balancetype='INR'))
                ).values('cbal')

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
    success_url = None

    def get_context_data(self,**kwargs):
        data = super(InvoiceCreateView,self).get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = InvoiceItemFormSet(self.request.POST)
        else:
            data['items'] = InvoiceItemFormSet()
        return data
  
    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        with transaction.atomic():
            form.instance.created_by = self.request.user
            self.object = form.save()
            if items.is_valid():
                items.instance = self.object
                items.save()
        return super(InvoiceCreateView,self).form_valid(form)
       
    def get_success_url(self) -> str:
        return reverse_lazy('purchase_invoice_detail',kwargs={'pk':self.object.pk})
   
class InvoiceDetailView(DetailView):
    model = Invoice

    def get_context_data(self, **kwargs):
        context = super(InvoiceDetailView, self).get_context_data(**kwargs)
        context['previous'] = self.object.get_previous()
        context['next'] = self.object.get_next()
        return context

class InvoiceUpdateView(UpdateView):
    model = Invoice
    form_class = InvoiceUpdateForm

    def get_context_data(self,**kwargs):
        data = super(InvoiceUpdateView,self).get_context_data(**kwargs)
        if self.object.posted:
            raise Http404
        if self.request.POST:
            data['items'] = InvoiceItemFormSet(self.request.POST,
                                                    instance = self.object)
        else:
            data['items'] = InvoiceItemFormSet(instance = self.object)
        return data

    @transaction.atomic()
    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']

        context = self.get_context_data()
        items = context['items']
        with transaction.atomic():
            self.object = form.save()
            if items.is_valid():
                items.instance = self.object
                items.save()
        return super(InvoiceUpdateView,self).form_valid(form)  
        
    def get_success_url(self) -> str:
        return reverse_lazy('purchase_invoice_detail', kwargs={'pk': self.object.pk})


@transaction.atomic()
def post_purchase(request,pk):
    # use get_objector404
    purchase_inv = Invoice.objects.get(id = pk)
    # post to dea & stock
    purchase_inv.post()
    return redirect(purchase_inv)


@transaction.atomic()
def unpost_purchase(request,pk):
    purchase_inv = Invoice.objects.get(id = pk)
    # unpost to dea & stock
    purchase_inv.unpost() 
    return redirect(purchase_inv)

from dea.models import Ledger,Journal,JournalTypes, LedgerTransaction,AccountTransaction
from moneyed import Money
@transaction.atomic()
def post_all_purchase(request):
    all_purchases = Invoice.objects.filter(posted = False).select_related('supplier')
    ledgers = dict(list(Ledger.objects.values_list('name', 'id')))
    lt = []
    at = []
    for purc in all_purchases:
        j = Journal.objects.create(
            content_type_id=40, object_id=purc.id, type=JournalTypes.PJ, desc='purchase')
        for i in purc.purchaseitems.all():
                i.post(j)

        money = Money(purc.balance,purc.balancetype)
            
        if purc.is_gst:
            inv = ledgers["GST INV"]
            tax = Money(purc.get_gst(), 'INR')
            amount = money + tax
        else:
            inv = ledgers["Non-GST INV"]
            amount = money

        lt.append(LedgerTransaction(journal = j,ledgerno_id = ledgers['Sundry Creditors'],ledgerno_dr_id = inv,amount =money))
        lt.append(LedgerTransaction(journal = j,ledgerno_id = ledgers['Sundry Creditors'],ledgerno_dr_id = ledgers['Input Igst'], amount = tax))
        at.append(AccountTransaction(journal = j,ledgerno_id = ledgers['Sundry Creditors'],XactTypeCode_id = 'Dr',XactTypeCode_ext_id = 'CRPU',
                    Account_id = purc.supplier.account.id,amount = amount))
    
    LedgerTransaction.objects.bulk_create(lt)
    AccountTransaction.objects.bulk_create(at)
    logger.warning('at and lt created successfully')

    all_purchases.update(posted=True)
    return HttpResponseRedirect(reverse('purchase_invoice_list'))


@transaction.atomic()
def unpost_all_purchase(request):
    all_purchases = Invoice.objects.filter(posted=True).select_related('supplier')
    ltl = []
    atl = []
    for purc in all_purchases:
        last_jrnl = purc.journals.latest()
        if last_jrnl.exists():
            jrnl = Journal.objects.create(content_object=purc,
                                      desc='purchase-revert')
            purc_items = purc.purchaseitems
            if purc_items.exists():
                for i in purc_items.all():
                    i.unpost(jrnl)
            ltxns = last_jrnl.ltxns.all()
            atxns = last_jrnl.atxns.all()
            for i in ltxns:
                ltl.append(LedgerTransaction(journal=jrnl, ledgerno_id=i.ledgerno_dr_id,
                                            ledgerno_dr_id=i.ledgerno_id, amount=i.amount))

            for i in atxns:
                if i.XactTypeCode_id == 'Cr':  # 1
                    atl.append(AccountTransaction(journal=jrnl, ledgerno_id=i.ledgerno_id, XactTypeCode_id='Dr',  # 2
                                                XactTypeCode_ext_id='AC', Account_id=i.Account_id, amount=i.amount))  # 1
                else:
                    atl.append(AccountTransaction(journal=jrnl, ledgerno_id=i.ledgerno_id, XactTypeCode_id='Cr',  # 1
                                                XactTypeCode_ext_id='AD', Account_id=i.Account_id, amount=i.amount))  # 2

        logger.warning('bulk creating lt and at')
        LedgerTransaction.objects.bulk_create(ltl)
        AccountTransaction.objects.bulk_create(atl)
    all_purchases.update(posted = False)

    return HttpResponseRedirect(reverse('purchase_invoice_list'))

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
        form.instance.created_by = self.request.user
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


@transaction.atomic()
def post_payment(request,pk):
    # use get_objector404
    payment = Payment.objects.get(id = pk)
    # post to dea
    payment.post()
    return redirect(payment)


@transaction.atomic()
def unpost_payment(request,pk):
    payment = Payment.objects.get(id = pk)
    # unpost to dea
    payment.unpost()
    return redirect(payment)


@transaction.atomic()
def post_all_payment(request):
    all_payts = Payment.objects.filter(posted=False)
    for i in all_payts:
        i.post()
    return reverse('purchase_payment_list')


@transaction.atomic()
def unpost_all_payment(request):
    all_payts = Payment.objects.filter(posted=False)
    for i in all_payts:
        i.unpost()
    return reverse('purchase_payment_list')
