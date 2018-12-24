from django.views.generic import DetailView, ListView, UpdateView, CreateView,DeleteView
from .models import Invoice, InvoiceItem, Receipt,ReceiptLine
from contact.models import Customer
from .forms import InvoiceForm, InvoiceItemForm, InvoiceItemFormSet,ReceiptForm,ReceiptLineForm,ReceiptLineFormSet
from django.http import HttpResponseRedirect,HttpResponse
from django.urls import reverse,reverse_lazy
from django_filters.views import FilterView
from .filters import InvoiceFilter,ReceiptFilter
from .render import Render
from num2words import num2words
from django.db.models import  Sum,Q,F,OuterRef,Subquery
from django.shortcuts import render

def print_invoice(request,id):
    invoice=Invoice.objects.get(id=id)
    params={'invoice':invoice}
    return Render.render('sales/invoice_pdf.html',params)

def print_receipt(request,id):
    receipt=Receipt.objects.get(id=id)
    params={'receipt':receipt,'inwords':num2words(receipt.total,lang='en_IN')}
    return Render.render('sales/receipt.html',params)

def list_balance(request):

    receipts=Receipt.objects.filter(customer=OuterRef('pk')).order_by().values('customer')
    grec=receipts.annotate(grec=Sum('total',filter=Q(type='Metal'))).values('grec')
    crec=receipts.annotate(crec=Sum('total',filter=Q(type='Cash'))).values('crec')
    invoices=Invoice.objects.filter(customer=OuterRef('pk')).order_by().values('customer')
    gbal=invoices.annotate(gbal=Sum('balance',filter=Q(paymenttype='Credit')&Q(balancetype='Metal'))).values('gbal')
    cbal=invoices.annotate(cbal=Sum('balance',filter=Q(paymenttype='Credit')&Q(balancetype='Cash'))).values('cbal')
    balance=Customer.objects.annotate(gbal=Subquery(gbal),grec=Subquery(grec),gold=F('gbal')-F('grec'),cbal=Subquery(cbal),crec=Subquery(crec),cash=F('cbal')-F('crec'))


    context={'balance':balance}
    return render(request,'sales/balance_list.html',context)

class InvoiceListView(FilterView):
    model = Invoice
    filterset_class = InvoiceFilter
    template_name = 'sales/invoice_list.html'

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

class ReceiptListView(FilterView):
    model = Receipt
    filterset_class = ReceiptFilter
    template_name = 'sales/receipt_list.html'

# class ReceiptCreateView(CreateView):
#     model = Receipt
#     form_class = ReceiptForm
class ReceiptCreateView(CreateView):
    model = Receipt
    form_class = ReceiptForm

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        receiptline_form = ReceiptLineFormSet()
        # for f in receiptline_form:
        #         f.fields['invoice'].queryset = Invoice.objects.filter(status="Unpaid")

        return self.render_to_response(
            self.get_context_data(form=form,
                                  receiptline_form=receiptline_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        receiptline_form = ReceiptLineFormSet(self.request.POST)
        # for f in receiptline_form:
        #         f.fields['invoice'].queryset = Invoice.objects.filter(status="Unpaid")
        if (form.is_valid() and receiptline_form.is_valid()):
            return self.form_valid(form, receiptline_form)
        else:
            return self.form_invalid(form, receiptline_form)

    def form_valid(self, form, receiptline_form):
        self.object = form.save()
        receiptline_form.instance = self.object
        items=receiptline_form.save()
        amount=self.object.total
        invpaid = 0
        for item in items:
            if item.invoice.balance == item.amount :
                invpaid += item.amount
                # Invoice.objects.filter(id=item.invoice.id).update(status="Paid")
                item.invoice.status="Paid"
                item.invoice.save()
            elif item.invoice.balance > item.amount:
                invpaid += item.amount
                # Invoice.objects.filter(id=item.invoice.id).update(status="PartiallyPaid")
                item.invoice.status="PartiallyPaid"
                item.invoice.save()

        # if amount > invpaid :
            # transfer amount to inv.customer account
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

class ReceiptDeleteView(DeleteView):
    model = Receipt
    success_url = reverse_lazy('sales_receipt_list')

class ReceiptLineCreateView(CreateView):
    model = ReceiptLine
    form_class = ReceiptLineForm

class ReceiptLineDeleteView(DeleteView):
    model = Receipt
    success_url = reverse_lazy('sales_receiptline_list')
