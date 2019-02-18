from django.views.generic import DetailView, ListView, UpdateView, CreateView,DeleteView
from .models import Invoice, InvoiceItem, Receipt,ReceiptLine,Month,Year
from contact.models import Customer
from .forms import InvoiceForm, InvoiceItemForm, InvoiceItemFormSet,ReceiptForm,ReceiptLineForm,ReceiptLineFormSet
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

class InvoiceListView(ExportMixin,SingleTableMixin,FilterView):
    model = Invoice
    table_class = InvoiceTable
    filterset_class = InvoiceFilter
    template_name = 'sales/invoice_list.html'
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
        self.object = form.save()

        invoiceitem_form.instance = self.object
        invoiceitem_form.save()

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

    def get(self, request, *args, **kwargs):

        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        invoiceitem_form = InvoiceItemFormSet(instance=self.object)

        return self.render_to_response(
            self.get_context_data(form=form,
                                  invoiceitem_form=invoiceitem_form))

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        invoiceitem_form = InvoiceItemFormSet(self.request.POST,instance=self.object)

        if (form.is_valid() and invoiceitem_form.is_valid()):
            return self.form_valid(form, invoiceitem_form)
        else:
            return self.form_invalid(form, invoiceitem_form)

    def form_valid(self, form, invoiceitem_form):

        self.object = form.save()
        invoiceitem_form.instance = self.object
        items=invoiceitem_form.save()

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
        amount=self.object.total
        # invpaid = 0
        # for item in items:
        #     if item.invoice.balance == item.amount :
        #         invpaid += item.amount
        #         item.invoice.status="Paid"
        #         item.invoice.save()
        #     elif item.invoice.balance > item.amount:
        #         invpaid += item.amount
        #         item.invoice.status="PartiallyPaid"
        #         item.invoice.save()

        # remaining=amount-invpaid

        # try:
        #     invtopay = Invoice.objects.filter(customer=self.object.customer,balancetype=self.object.type).exclude(status="Paid").order_by('created')[0]
        # except IndexError:
        #     invtopay = None
        # print(invtopay)
        # while remaining>0 and invtopay !=None:
        #
        #     if remaining >= invtopay.get_balance() :
        #         remaining -= invtopay.get_balance()
        #         ReceiptLine.objects.create(receipt=self.object,invoice=invtopay,amount=invtopay.get_balance())
        #         invtopay.status="Paid"
        #     else :
        #         ReceiptLine.objects.create(receipt=self.object,invoice=invtopay,amount=remaining)
        #         invtopay.status="PartiallyPaid"
        #         remaining=0
        #     invtopay.save()
        #     try:
        #         invtopay = Invoice.objects.filter(customer=self.object.customer,balancetype=self.object.type).exclude(status="Paid").order_by('created')[0]
        #     except IndexError:
        #         invtopay = None
        try:
            invtopay = Invoice.objects.filter(customer=self.object.customer,balancetype=self.object.type).exclude(status="Paid").order_by('created')
        except IndexError:
            invtopay = None
        print(invtopay)
        for i in invtopay:
            print(i)
            if amount<=0 : break
            bal=i.get_balance()
            if amount >= bal :
                amount -= bal
                ReceiptLine.objects.create(receipt=self.object,invoice=i,amount=bal)
                i.status="Paid"
            else :
                ReceiptLine.objects.create(receipt=self.object,invoice=i,amount=amount)
                i.status="PartiallyPaid"
                amount=0
            i.save()

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
        amount=self.object.total
        invpaid = self.object.get_line_totals()
        # experimental
        if invpaid is None:
            invpaid=0
        for item in items:
            if item.invoice.balance == item.amount :
                invpaid += item.amount
                item.invoice.status="Paid"
                item.invoice.save()
            elif item.invoice.balance > item.amount:
                invpaid += item.amount
                item.invoice.status="PartiallyPaid"
                item.invoice.save()
        # end experimental
        remaining=amount-invpaid
        try:
            invtopay = Invoice.objects.filter(customer=self.object.customer,balancetype=self.object.type).exclude(status="Paid").order_by('created')[0]
        except IndexError:
            invtopay = None
        while remaining>0 and invtopay !=None:
            if remaining >= invtopay.get_balance() :
                remaining -= invtopay.get_balance()
                ReceiptLine.objects.create(receipt=self.object,invoice=invtopay,amount=invtopay.get_balance())
                invtopay.status="Paid"
            else :
                ReceiptLine.objects.create(receipt=self.object,invoice=invtopay,amount=remaining)
                invtopay.status="PartiallyPaid"
                remaining=0
            invtopay.save()
            try:
                invtopay = Invoice.objects.filter(customer=self.object.customer,balancetype=self.object.type).exclude(status="Paid").order_by('created')[0]
            except IndexError:
                invtopay = None

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, receiptline_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(
            self.get_context_data(form=form,
                                  receiptline_form=receiptline_form))

class ReceiptDeleteView(DeleteView):
    model = Receipt
    success_url = reverse_lazy('sales_receipt_list')

class ReceiptLineCreateView(CreateView):
    model = ReceiptLine
    form_class = ReceiptLineForm

class ReceiptLineDeleteView(DeleteView):
    model = ReceiptLine
    success_url = reverse_lazy('sales_receiptline_list')
