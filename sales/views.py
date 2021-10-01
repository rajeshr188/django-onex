from django.http.response import Http404
from django.views.generic import DetailView, ListView, UpdateView, CreateView,DeleteView
from .models import Invoice, InvoiceItem, Receipt,ReceiptLine,Month,Year
from contact.models import Customer
from .forms import (InvoiceForm, InvoiceItemForm, InvoiceItemFormSet,ReceiptForm,
                    ReceiptLineForm,ReceiptItemFormSet,RandomSalesForm)
from django.http import HttpResponseRedirect
from django.urls import reverse,reverse_lazy
from django_filters.views import FilterView
from .filters import InvoiceFilter,ReceiptFilter
from .render import Render
from num2words import num2words
from django.db.models import  Sum,Q,F,OuterRef,Subquery
from django.db.models.functions import Coalesce,TruncMonth,TruncYear
from django.shortcuts import render,redirect
from django_tables2.views import SingleTableMixin
from django_tables2.export.views import ExportMixin
from .tables import InvoiceTable,ReceiptTable
from django.http import JsonResponse,HttpResponseRedirect
from django.db import transaction
import logging

logger = logging.getLogger(__name__)
def home(request):
    
    context = {}
    qs = Invoice.objects
    qs_posted = qs.posted()
    avgrate = qs_posted.avg_rate()
    total = dict()
    total['total']=qs_posted.total_with_ratecut()
    if total['total']['cash']:
        total['total']['gmap'] = round(avgrate['gold'],2)
        total['total']['smap'] = round(avgrate['silver'],2)
        
    else:
        total['total']['gmap']=0
        total['total']['smap'] = 0
    
    gst_avgrate = qs_posted.gst().avg_rate()
    total['gst'] = qs_posted.gst().total_with_ratecut()
    if total['gst']['cash']: 
        total['gst']['gmap'] = round(gst_avgrate['gold'], 2)
        total['gst']['smap'] = round(gst_avgrate['silver'], 2)
       
    else:
        total['gst']['gmap']=0
        total['gst']['smap']=0
    
    total['nongst'] = qs_posted.non_gst().total_with_ratecut()
    nongst_avgrate = qs_posted.non_gst().avg_rate()
    if total['nongst']['cash']:
        total['nongst']['gmap'] = round(nongst_avgrate['gold'], 2)
        total['nongst']['smap'] = round(nongst_avgrate['silver'], 2)
       
    else:
        total['nongst']['gmap']=0
        total['nongst']['smap']=0
    context['total']=total
    return render(request,'sales/home.html',context)

def randomsales(request):
    c=Customer.objects.order_by("?")[:30]

    if request.method == 'POST':
        form = RandomSalesForm(request.POST)
        if form.is_valid():
            print('success')
    else:
        form = RandomSalesForm()

    data = dict()
    data['cust']=c

    return render(request, 'sales/randomsales.html', context={'data':data,'form':form},)

def print_invoice(request,pk):
    invoice=Invoice.objects.get(id=pk)
    params={'invoice':invoice}
    return Render.render('sales/invoice_pdf.html',params)

def print_receipt(request,pk):
    receipt=Receipt.objects.get(id=pk)
    params={'receipt':receipt,'inwords':num2words(receipt.total,lang='en_IN')}
    return Render.render('sales/receipt.html',params)

def list_balance(request):

    receipts=Receipt.objects.filter(customer=OuterRef('pk')).order_by().values('customer')
    grec=receipts.annotate(grec=Sum('total',filter=Q(type='Gold'))).values('grec')
    crec=receipts.annotate(crec=Sum('total',filter=Q(type='Cash'))).values('crec')

    invoices=Invoice.objects.filter(customer=OuterRef('pk')).\
                order_by().values('customer')
    gbal=invoices.annotate(gbal=Sum('balance',
            filter=Q(balancetype='Gold'))).values('gbal')
    cbal=invoices.annotate(cbal=Sum('balance',
            filter=Q(balancetype='Cash'))).values('cbal')

    balance=Customer.objects.filter(type='Wh').values('id','name').\
                annotate(gbal=Subquery(gbal),grec=Subquery(grec),gold=F('gbal')-F('grec'),
                        cbal=Subquery(cbal),crec=Subquery(crec),cash=F('cbal')-F('crec')).\
                        order_by('name')

    balance_total = balance.aggregate(gbal_total = Coalesce(Sum(F('gbal')),0),
                    grec_total = Coalesce(Sum(F('grec')),0),
                    cbal_total = Coalesce(Sum(F('cbal')),0),
                    crec_total = Coalesce(Sum(F('crec')),0))

    balance_nett_gold = balance_total['gbal_total']  - balance_total['grec_total']
    balance_nett_cash = balance_total['cbal_total']-balance_total['crec_total']

    balance_by_month = Invoice.objects.annotate(month = Month('created')).\
                        values('month').order_by('month').\
                        annotate(tc = Sum('balance',filter = Q(balancetype='Cash')),tm = Sum('balance',filter = Q(balancetype = 'Metal')))

    context={'balance':balance,'balance_total':balance_total,
                'balance_nett_gold':balance_nett_gold,
                'balance_nett_cash':balance_nett_cash,
                'balance_by_month':balance_by_month,

    }
    return render(request,'sales/balance_list.html',context)

def graph(request):
    return render(request, 'sales/graph.html')

def sales_count_by_month(request):
    # data = Invoice.objects.extra(select={'date': 'DATE(created)'},order_by=['date']).values('date').annotate(count_items=Count('id'))
    data = Invoice.objects.annotate(month = Month('created')).values('month').\
            order_by('month').annotate(tc = Sum('balance',filter = Q(balancetype='Metal')))
    return JsonResponse(list(data), safe=False)

import tablib
from .admin import InvoiceResource,ReceiptResource
from openpyxl import load_workbook
import re
import pytz

def simple_upload(request):
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        # fs = FileSystemStorage()
        # filename = fs.save(myfile.name, myfile)
        # uploaded_file_url = fs.url(filename)
        wb=load_workbook(myfile,read_only=True)
        sheet = wb.active

        inv = tablib.Dataset(headers = ['id','customer','created','description','balancetype','balance'])
        rec = tablib.Dataset(headers = ['id','customer','created','description','type','total',])
        bal = tablib.Dataset(headers = ['customer','cash_balance','metal_balance'])
        pname = None
        for row in sheet.rows:
            if row[0].value is not None and 'Sundry Debtors' in row[0].value:
                pname = re.search(r'\)\s([^)]+)', row[0].value).group(1).strip()
            elif pname is not None and row[0].value is None:
                if row[1].value is not None:
                    date = pytz.utc.localize(row[1].value)
                    # id = re.search(r'\:\s([^)]+)', row[3].value).group(1).strip()
                    if row[4].value is not None:
                        inv_list = ['', pname,date,
                           row[2].value,'Cash',  row[4].value]
                        inv.append(inv_list)
                    if row[9].value is not None:
                        rec_list = ['',pname, date,
                            row[2].value, 'Cash', row[9].value]
                        rec.append(rec_list)
                    if row[22].value is not None:
                        inv_list = ['',pname, date,
                            row[2].value,'Gold', row[22].value]
                        inv.append(inv_list)
                    if row[24].value is not None:
                        rec_list = ['',pname, date,
                            row[2].value,'Gold', row[24].value]
                        rec.append(rec_list)
                elif row[1].value is None and (row[4].value and row[16].value and row[26].value is not None):
                    bal_list = [pname,row[16].value,row[26].value]
                    bal.append(bal_list)
        # print(bal.export('csv'))
        inv_r = InvoiceResource()
        rec_r = ReceiptResource()

        print("running  inv wet run")
        inv_result = inv_r.import_data(inv, dry_run=False)  # Test the data import
        print("running  rec wet run")
        rec_result = rec_r.import_data(rec,dry_run=False)
        print("succesfuly imported")
        # if not inv_result.has_errors():
        #     print("running wet")
        #     inv_r.import_data(inv, dry_run=False)  # Actually import now
        # else :
        #     print("error occured")
        # if not rec_result.has_errors():
        #     rec_r.import_data(dataset, dry_run=False)  # Actually import now

        return render(request, 'sales/simpleupload.html')

    return render(request, 'sales/simpleupload.html')

class InvoiceListView(ExportMixin,SingleTableMixin,FilterView):
    model = Invoice
    table_class = InvoiceTable
    filterset_class = InvoiceFilter
    template_name = 'sales/invoice_list.html'
    paginate_by = 25

from approval.models import Approval
class InvoiceCreateView(CreateView):
    model = Invoice
    form_class = InvoiceForm
    success_url = None

    def get_context_data(self,*args,**kwargs):
        data = super(InvoiceCreateView,self).get_context_data(*args,**kwargs)
        if self.request.method == 'POST':
            data['items'] = InvoiceItemFormSet(self.request.POST)
        else:
            data['items'] = InvoiceItemFormSet()
            if 'approvalid' in self.request.GET:
                
                approval = Approval.objects.get(id=self.request.GET['approvalid'])
                approvallines = approval.items.filter(status='Pending').values()
                data['form'].fields["customer"].queryset = Customer.objects.filter(
                    id=approval.contact.id)
                data['form'].fields["approval"].initial = approval

                for subform, da in zip(data['items'].forms, approvallines):
                    da.pop('id')
                    subform.initial = da  
        return data

    def form_valid(self,form):
        context = self.get_context_data()
        items = context['items']
        with transaction.atomic():
            form.instance.created_by = self.request.user
            self.object = form.save()
            if items.is_valid():
                items.instance = self.object
                items.save()
        return super(InvoiceCreateView, self).form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy('sales_invoice_detail', kwargs={'pk': self.object.pk})

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
        # prevent update if posted
        if self.object.posted:
            raise Http404
        if self.request.POST:
            data['items'] = InvoiceItemFormSet(self.request.POST,instance = self.object)
        else:
            data['items'] = InvoiceItemFormSet(instance = self.object)
        return data

    @transaction.atomic()
    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']

        with transaction.atomic():
            self.object = form.save()
            if items.is_valid():
                items.instance = self.object
                items.save()
        return super(InvoiceCreateView, self).form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy('sales_invoice_detail', kwargs={'pk': self.object.pk})
                                  
@transaction.atomic()
def post_sales(request,pk):
    sales_inv = Invoice.objects.get(id = pk)
    sales_inv.post()
    return redirect(sales_inv)

@transaction.atomic()
def unpost_sales(request,pk):
    sales_inv = Invoice.objects.get(id = pk)
    sales_inv.unpost()
    sales_inv.posted = False
    sales_inv.save(update_fields=['posted'])
    return redirect(sales_inv)

# @transaction.atomic()
# def post_allsales(request):
#     all_sales = Invoice.objects.filter(posted = False)
#     from dea.models import Ledger
#     ledgers = dict(list(Ledger.objects.values_list('name', 'id')))
#     for i in all_sales:
#         logger.warning(f"posting journals for {i.id}")
#         i.post(ledgers = ledgers)  
#     all_sales.update(posted = True)
#     return HttpResponseRedirect(reverse('sales_invoice_list'))

from dea.models import Ledger,Journal,JournalTypes, LedgerTransaction,AccountTransaction
from approval.models import ApprovalLineReturn
from moneyed import Money
@transaction.atomic()
def post_allsales(request):
    all_sales = Invoice.objects.filter(posted = False).select_related('customer')
    ledgers = dict(list(Ledger.objects.values_list('name', 'id')))
    lt = []
    at = []
    for sale in all_sales:
        j = Journal.objects.create(content_type_id =35,object_id = sale.id,type = JournalTypes.SJ,desc = 'sale')
        if sale.approval:
            for i in sale.approval.items.filter(status='Pending'):
                apr = ApprovalLineReturn.objects.create(
                line=i, quantity=i.quantity, weight=i.weight)
                apr.post()
                i.update_status()
                sale.approval.is_billed = True
                sale.approval.save()
                sale.approval.update_status()
        if sale.saleitems.exists():
            for i in sale.saleitems.all():
                i.post(j)

        money = Money(sale.balance, sale.balancetype)

        if sale.is_gst:
            inv = ledgers["GST INV"]
            cogs = ledgers["GST COGS"]
            gst = Money(sale.gst(),'INR')
            amount = money + gst

        else:
            inv = ledgers["Non-GST INV"]
            cogs = ledgers["Non-GST COGS"]
            amount = money
            gst = Money(0,'INR')

        lt.append(LedgerTransaction(journal_id = j.id,ledgerno_id = ledgers['Sales'], ledgerno_dr_id =  ledgers['Sundry Debtors'], amount = money))
        lt.append(LedgerTransaction(journal_id = j.id,ledgerno_id = inv, ledgerno_dr_id = cogs, amount = money))
        lt.append(LedgerTransaction(journal_id = j.id,ledgerno_id =ledgers['Output Igst'],ledgerno_dr_id = ledgers['Sundry Debtors'],amount = gst))
        at.append(AccountTransaction(journal_id =j.id,ledgerno_id = ledgers['Sales'],XactTypeCode_id = 'Cr', XactTypeCode_ext_id = 'CRSL',
                 Account_id = sale.customer.account.id,amount = amount))

    LedgerTransaction.objects.bulk_create(lt)
    AccountTransaction.objects.bulk_create(at)
    logger.warning('at and lt created successfully')

    all_sales.update(posted=True)
    return HttpResponseRedirect(reverse('sales_invoice_list'))

# def post_allsales(request):
#     all_sales = Invoice.objects.values_list('id',flat = True)
#     ledgers = dict(list(Ledger.objects.values_list('name', 'id')))

#     j_objs = []
#     for i in all_sales:
#         j_objs.append(Journal(content_type_id =35,object_id = i,type = JournalTypes.SJ,desc = 'sale'))


#     js = Journal.objects.bulk_create(j_objs)
#     logger.warning('journals created successfully')
#     lt =[]
#     at=[]
#     for i in js:
#         sale = i.content_object
#         if sale.approval:
#            for i in sale.approval.items.filter(status='Pending'):
#                apr = ApprovalLineReturn.objects.create(
#                    line=i, quantity=i.quantity, weight=i.weight)
#                apr.post()
#                i.update_status()
#                sale.approval.is_billed = True
#                sale.approval.save()
#                sale.approval.update_status()
#         if sale.saleitems.exists():
#             for i in sale.saleitems.all():
#                 i.post(i)
            
#         money = Money(sale.balance, sale.balancetype)
            
#         if sale.is_gst:
#             inv = ledgers["GST INV"]
#             cogs = ledgers["GST COGS"]
#             gst = Money(sale.gst(),'INR')
#             amount = money + gst
               
#         else:
#             inv = ledgers["Non-GST INV"]
#             cogs = ledgers["Non-GST COGS"]
#             amount = money
#             gst = Money(0,'INR')
            
#         lt.append(LedgerTransaction(journal_id = i.id,ledgerno_id = ledgers['Sales'], ledgerno_dr_id =  ledgers['Sundry Debtors'], amount = money))
#         lt.append(LedgerTransaction(journal_id = i.id,ledgerno_id = inv, ledgerno_dr_id = cogs, amount = money))
#         lt.append(LedgerTransaction(journal_id = i.id,ledgerno_id =ledgers['Output Igst'],ledgerno_dr_id = ledgers['Sundry Debtors'],amount = gst))
#         at.append(AccountTransaction(journal_id =i.id,ledgerno_id = ledgers['Sales'],XactTypeCode_id = 'Cr', XactTypeCode_ext_id = 'CRSL',
#                    Account_id = sale.customer.account.id,amount = amount))

#     LedgerTransaction.objects.bulk_create(lt)
#     AccountTransaction.objects.bulk_create(at)
#     logger.warning('at and lt created successfully')

#     all_sales.update(posted=True)
#     return HttpResponseRedirect(reverse('sales_invoice_list'))

@transaction.atomic()
def unpost_allsales(request):
    all_sales = Invoice.objects.filter(posted = True).select_related('customer')
    logger.warning('retreived sales')
    ltl = []
    atl = []
    for sale in all_sales:
        last_jrnl = sale.journals.latest()
        jrnl = Journal.objects.create(content_object=sale,
                                         desc='sale-revert')
        if sale.approval:
            sale.approval.is_billed = False
            approval_items = sale.approval.items.all()
            for i in approval_items:
                i.unpost()
                i.product.add(i.weight, i.quantity, i, 'A')
                i.update_status()
            sale.approval.save()
            sale.approval.update_status()

        sale_items = sale.saleitems
        if sale.saleitems.exists():
            for i in sale_items.all():
                i.unpost(jrnl)

        ltxns = last_jrnl.ltxns.all()
        atxns = last_jrnl.atxns.all()

        for i in ltxns:
            ltl.append(LedgerTransaction(journal=jrnl, ledgerno_id=i.ledgerno_dr_id,
                                             ledgerno_dr_id=i.ledgerno_id, amount=i.amount))
            
        
        for i in atxns:
            if i.XactTypeCode_id == 'Cr':  # 1
                atl.append(AccountTransaction(journal = jrnl, ledgerno_id = i.ledgerno_id, XactTypeCode_id = 'Dr',#2
                        XactTypeCode_ext_id = 'AC' , Account_id = i.Account_id, amount = i.amount))#1
            else:
                atl.append(AccountTransaction(journal = jrnl, ledgerno_id = i.ledgerno_id, XactTypeCode_id = 'Cr',#1
                        XactTypeCode_ext_id = 'AD' , Account_id = i.Account_id, amount = i.amount))   #2

    logger.warning('bulk creating lt and at')
    LedgerTransaction.objects.bulk_create(ltl)
    AccountTransaction.objects.bulk_create(atl)
    all_sales.update(posted = False)
    return HttpResponseRedirect(reverse('sales_invoice_list'))

class InvoiceDeleteView(DeleteView):
    model = Invoice
    success_url = reverse_lazy('sales_invoice_list')

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

class InvoiceItemDeleteView(DeleteView):
    model = InvoiceItem
    success_url = reverse_lazy('sales_invoiceitem_list')

class ReceiptListView(ExportMixin,SingleTableMixin,FilterView):
    model = Receipt
    table_class=ReceiptTable
    filterset_class = ReceiptFilter
    template_name = 'sales/receipt_list.html'
    paginate_by = 25

class ReceiptCreateView(CreateView):
    model = Receipt
    form_class = ReceiptForm

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        receiptitem_form = ReceiptItemFormSet()

        return self.render_to_response(
            self.get_context_data(form=form,
                                  receiptitem_form=receiptitem_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        receiptitem_form = ReceiptItemFormSet(self.request.POST)
        if (form.is_valid() and receiptitem_form.is_valid()):
            return self.form_valid(form, receiptitem_form)
        else:
            return self.form_invalid(form, receiptitem_form)

    def form_valid(self, form, receiptitem_form):
        form.instance.created_by = self.request.user
        self.object = form.save()
        receiptitem_form.instance = self.object
        receiptitem_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, receiptitem_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(
            self.get_context_data(form=form,
                                  receiptline_form=receiptitem_form))

@transaction.atomic()
def post_receipt(request, pk):
    rcpt = Receipt.objects.get(id=pk)
    rcpt.post()
    return redirect(rcpt)

@transaction.atomic()
def unpost_receipt(request, pk):
    rcpt = Receipt.objects.get(id=pk)
    rcpt.unpost()
    return redirect(rcpt)
    
@transaction.atomic()
def post_allrcpts(request):
    all_rcpts = Receipt.objects.filter(posted = False)
    for i in all_rcpts:
        i.post()
    return reverse('sales_receipt_list')

@transaction.atomic()
def unpost_allrcpts(request):
    all_rcpts = Receipt.objects.filter(posted=True)
    for i in all_rcpts:
        i.unpost()
    return reverse('sales_receipt_list')

class ReceiptDetailView(DetailView):
    model = Receipt

class ReceiptUpdateView(UpdateView):
    model = Receipt
    form_class = ReceiptForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        receiptitem_form = ReceiptItemFormSet(instance=self.object)

        return self.render_to_response(
            self.get_context_data(form=form,
                                  receiptitem_form=receiptitem_form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        receiptitem_form = ReceiptItemFormSet(self.request.POST,instance=self.object)
        if (form.is_valid() and receiptitem_form.is_valid()):
            return self.form_valid(form, receiptitem_form)
        else:
            return self.form_invalid(form, receiptitem_form)

    def form_valid(self, form, receiptitem_form):
        self.object = form.save()

        receiptitem_form.instance = self.object
        items=receiptitem_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, receiptitem_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(
            self.get_context_data(form=form,
                                  receiptitem_form=receiptitem_form))

# create a function view on receipt list page  to reallot all receipts

class ReceiptDeleteView(DeleteView):
    model = Receipt
    success_url = reverse_lazy('sales_receipt_list')

class ReceiptLineCreateView(CreateView):
    model = ReceiptLine
    form_class = ReceiptLineForm

class ReceiptLineUpdateView(UpdateView):
    model = ReceiptLine
    form = ReceiptLineForm

class ReceiptLineDeleteView(DeleteView):
    model = ReceiptLine
    success_url = reverse_lazy('sales_receiptline_list')
