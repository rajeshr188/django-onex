from django.views.generic import DetailView, ListView, UpdateView, CreateView,DeleteView
from .models import Invoice, InvoiceItem, Receipt,ReceiptLine,Month,Year
from contact.models import Customer
from .forms import (InvoiceForm, InvoiceItemForm, InvoiceItemFormSet,ReceiptForm,
                    ReceiptLineForm,ReceiptLineFormSet,RandomSalesForm)
from django.http import HttpResponseRedirect,HttpResponse
from django.urls import reverse,reverse_lazy
from django_filters.views import FilterView
from .filters import InvoiceFilter,ReceiptFilter
from .render import Render
from num2words import num2words
from django.db.models import  Sum,Q,F,OuterRef,Subquery,Count
from django.db.models.functions import TruncMonth,Coalesce
from django.shortcuts import render
from django_tables2 import RequestConfig
from django_tables2.views import SingleTableMixin
from django_tables2.export.views import ExportMixin
from .tables import InvoiceTable,ReceiptTable
from django.http import JsonResponse
import json
from product.models import Stree
from django.db import transaction

def home(request):
    inv = Invoice.objects
    sales_by_month=inv.annotate(month = Month('created'),year=Year('created')).\
                    values('year','month').order_by('month').\
                    annotate(tc = Coalesce(Sum('balance',filter = Q(balancetype='Cash')),0),
                            tm = Coalesce(Sum('balance',filter = Q(balancetype = 'Metal')),0))
    rec = Receipt.objects
    receipts_by_month = rec.annotate(month = Month('created'),year=Year('created')).\
                    values('month','year').order_by('month').\
                    annotate(tc = Sum('total',filter = Q(type='Cash')),tm = Sum('total',filter = Q(type = 'Metal')))
    data = dict()
    data['sales_by_month']=sales_by_month
    # var_fixed = []
    # for row in (sales_by_month):
    #     var_fixed.append([str(row[0]),int(float(row[1]))])

    data['saleslist']=sales_by_month
    data['receipts_by_month']=receipts_by_month
    return render(request,'sales/home.html',context={'data':data},)

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

    now = datetime.datetime.now()
    daterange = calendar.monthrange(now.year,now.month)
    row = dict()



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
    grec=receipts.annotate(grec=Sum('total',filter=Q(type='Metal'))).values('grec')
    crec=receipts.annotate(crec=Sum('total',filter=Q(type='Cash'))).values('crec')

    invoices=Invoice.objects.filter(customer=OuterRef('pk')).\
                order_by().values('customer')
    gbal=invoices.annotate(gbal=Sum('balance',
            filter=Q(paymenttype='Credit')&Q(balancetype='Metal'))).values('gbal')
    cbal=invoices.annotate(cbal=Sum('balance',
            filter=Q(paymenttype='Credit')&Q(balancetype='Cash'))).values('cbal')

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


from django.conf import settings
# from django.core.files.storage import FileSystemStorage
import tablib
from .admin import InvoiceResource,ReceiptResource
import openpyxl
import datetime
from openpyxl import Workbook,load_workbook
import re
import time
import pytz
def simple_upload(request):
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        # fs = FileSystemStorage()
        # filename = fs.save(myfile.name, myfile)
        # uploaded_file_url = fs.url(filename)
        wb=load_workbook(myfile,read_only=True)
        sheet = wb.active

        inv = tablib.Dataset(headers = ['id','customer','created','description','balancetype','paymenttype','balance'])
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
                           row[2].value,'Cash','Credit',  row[4].value]
                        inv.append(inv_list)
                    if row[9].value is not None:
                        rec_list = ['',pname, date,
                            row[2].value, 'Cash', row[9].value]
                        rec.append(rec_list)
                    if row[22].value is not None:
                        inv_list = ['',pname, date,
                            row[2].value,'Metal','Credit', row[22].value]
                        inv.append(inv_list)
                    if row[24].value is not None:
                        rec_list = ['',pname, date,
                            row[2].value,'Metal', row[24].value]
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

from approval.models import Approval,ApprovalLine
class InvoiceCreateView(CreateView):
    model = Invoice
    form_class = InvoiceForm

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        invoiceitem_form = InvoiceItemFormSet()
        if 'approvalid' in request.GET:
            aid = request.GET['approvalid']
            print(aid)
            approval = Approval.objects.get(id = aid)
            approvallines = approval.approvalline_set.values()
            print(approvallines)
            form.fields['customer'].queryset = Customer.objects.filter(id=approval.contact.id)
            for subform, data in zip(invoiceitem_form.forms, approvallines):
                subform.initial = data
                print(data)
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

    @transaction.atomic()
    def form_valid(self, form, invoiceitem_form):
        self.object = form.save()
        invoiceitem_form.instance = self.object
        try:
            invoiceitem_form.save()
        except Exception:
            # raise Exception("Failed Form Save")
            self.object.delete()
            form.add_error(None,'error i n transfer')
            return self.form_invalid(form = form,invoiceitem_form = invoiceitem_form)

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

class InvoiceUpdateView(UpdateView):
    model = Invoice
    form_class = InvoiceForm

    def get_context_data(self,*args,**kwargs):
        data = super(InvoiceUpdateView,self).get_context_data(**kwargs)
        if self.request.POST:
            data['invoiceitem_form'] = InvoiceItemFormSet(self.request.POST,instance = self.object)
        else:
            data['invoiceitem_form'] = InvoiceItemFormSet(instance = self.object)
        return data

    @transaction.atomic()
    def form_valid(self, form):
        context = self.get_context_data()
        invoiceitem_form = context['invoiceitem_form']

        self.object = form.save()
        print(invoiceitem_form.is_valid())
        if invoiceitem_form.is_valid():
            try:
                invoiceitem_form.save()
            except Exception:
                # raise Exception("Failed Form Save")
                form.add_error(None,'error in transfer qty or wt mismatch')
                return self.form_invalid(form = form,invoiceitem_form = invoiceitem_form)

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, invoiceitem_form):
        return self.render_to_response(
            self.get_context_data(form=form,
                                  invoiceitem_form=invoiceitem_form))


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
        receiptline_form = ReceiptLineFormSet()

        return self.render_to_response(
            self.get_context_data(form=form,
                                  receiptline_form=receiptline_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        receiptline_form = ReceiptLineFormSet(self.request.POST)
        if (form.is_valid() and receiptline_form.is_valid()):
            return self.form_valid(form, receiptline_form)
        else:
            return self.form_invalid(form, receiptline_form)

    def form_valid(self, form, receiptline_form):
        self.object = form.save()
        receiptline_form.instance = self.object
        receiptline_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, receiptline_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(
            self.get_context_data(form=form,
                                  receiptline_form=receiptline_form))

class ReceiptDetailView(DetailView):
    model = Receipt

class ReceiptUpdateView(UpdateView):
    model = Receipt
    form_class = ReceiptForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        receiptline_form = ReceiptLineFormSet(instance=self.object)

        return self.render_to_response(
            self.get_context_data(form=form,
                                  receiptline_form=receiptline_form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        receiptline_form = ReceiptLineFormSet(self.request.POST,instance=self.object)
        if (form.is_valid() and receiptline_form.is_valid()):
            return self.form_valid(form, receiptline_form)
        else:
            return self.form_invalid(form, receiptline_form)

    def form_valid(self, form, receiptline_form):
        self.object = form.save()

        receiptline_form.instance = self.object
        items=receiptline_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, receiptline_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(
            self.get_context_data(form=form,
                                  receiptline_form=receiptline_form))

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
