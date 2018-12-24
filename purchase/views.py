from django.views.generic import DetailView, ListView, UpdateView, CreateView
from .models import Invoice, InvoiceItem, Payment,PaymentLine
from contact.models import Supplier
from .forms import InvoiceForm, InvoiceItemForm,InvoiceItemFormSet, PaymentForm,PaymentLineForm,PaymentLineFormSet
from django.http import HttpResponseRedirect,HttpResponse
from django.urls import reverse,reverse_lazy
from django_filters.views import FilterView
from .filters import InvoiceFilter,PaymentFilter
from .render import Render
from num2words import num2words
from django.db.models import  Sum,Q,F,OuterRef,Subquery
from django.shortcuts import render

def print_invoice(request,id):
    invoice=Invoice.objects.get(id=id)
    params={'invoice':invoice}
    return Render.render('purchase/invoice_pdf.html',params)

def print_payment(request,id):
    payment=Payment.objects.get(id=id)
    params={'payment':payment,'inwords':num2words(payment.total,lang='en_IN')}
    return Render.render('purchase/payment.html',params)

def list_balance(request):

    payments=Payment.objects.filter(supplier=OuterRef('pk')).order_by().values('supplier')
    grec=payments.annotate(grec=Sum('total',filter=Q(type='Metal'))).values('grec')
    crec=payments.annotate(crec=Sum('total',filter=Q(type='Cash'))).values('crec')
    invoices=Invoice.objects.filter(supplier=OuterRef('pk')).order_by().values('supplier')
    gbal=invoices.annotate(gbal=Sum('balance',filter=Q(paymenttype='Credit')&Q(balancetype='Metal'))).values('gbal')
    cbal=invoices.annotate(cbal=Sum('balance',filter=Q(paymenttype='Credit')&Q(balancetype='Cash'))).values('cbal')
    balance=Supplier.objects.annotate(gbal=Subquery(gbal),grec=Subquery(grec),gold=F('gbal')-F('grec'),cbal=Subquery(cbal),crec=Subquery(crec),cash=F('cbal')-F('crec'))


    context={'balance':balance}
    return render(request,'sales/balance_list.html',context)

class InvoiceListView(FilterView):
    model = Invoice
    filterset_class = InvoiceFilter
    template_name = 'purchase/invoice_list.html'

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


class PaymentListView(FilterView):
    model = Payment
    filterset_class = PaymentFilter
    template_name="purchase/payment_list.html"

class PaymentCreateView(CreateView):
    model = Payment
    form_class = PaymentForm

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        paymentline_form = PaymentLineFormSet()

        return self.render_to_response(
            self.get_context_data(form=form,
                                  paymentline_form=paymentline_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        paymentline_form = PaymentLineFormSet(self.request.POST)
        # for f in paymentline_form:
        #         f.fields['invoice'].queryset = Invoice.objects.filter(status="Unpaid")
        if (form.is_valid() and paymentline_form.is_valid()):
            return self.form_valid(form, paymentline_form)
        else:
            return self.form_invalid(form, paymentline_form)

    def form_valid(self, form, paymentline_form):
        self.object = form.save()
        paymentline_form.instance = self.object
        items=paymentline_form.save()
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

    def form_invalid(self, form, paymentline_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(
            self.get_context_data(form=form,
                                  paymentline_form=paymentline_form))



class PaymentDetailView(DetailView):
    model = Payment


class PaymentUpdateView(UpdateView):
    model = Payment
    form_class = PaymentForm

class PaymentLineCreateView(CreateView):
    model = PaymentLine
    form_class = PaymentLineForm
