from django.views.generic import DetailView, ListView, UpdateView, CreateView,DeleteView
from .models import Invoice, InvoiceItem, Payment,PaymentLine
from contact.models import Customer
from .forms import InvoiceForm, InvoiceItemForm,InvoiceItemFormSet, PaymentForm,PaymentLineForm,PaymentLineFormSet
from django.http import HttpResponseRedirect,HttpResponse
from django.urls import reverse,reverse_lazy
from django_filters.views import FilterView
from .filters import InvoiceFilter,PaymentFilter
from .render import Render
from num2words import num2words
from django.db.models import  Sum,Q,F,OuterRef,Subquery
from django.shortcuts import render
from django_tables2 import RequestConfig
from django_tables2.views import SingleTableMixin
from django_tables2.export.views import ExportMixin
from .tables import InvoiceTable,PaymentTable

def print_invoice(request,pk):
    invoice=Invoice.objects.get(id=pk)
    params={'invoice':invoice}
    return Render.render('purchase/invoice_pdf.html',params)

def print_payment(request,pk):
    payment=Payment.objects.get(id=pk)
    params={'payment':payment,'inwords':num2words(payment.total,lang='en_IN')}
    return Render.render('purchase/payment.html',params)

def list_balance(request):

    payments=Payment.objects.filter(supplier=OuterRef('pk')).order_by().values('supplier')
    grec=payments.annotate(grec=Sum('total',filter=Q(type='Metal'))).values('grec')
    crec=payments.annotate(crec=Sum('total',filter=Q(type='Cash'))).values('crec')
    invoices=Invoice.objects.filter(supplier=OuterRef('pk')).order_by().values('supplier')
    gbal=invoices.annotate(gbal=Sum('balance',filter=Q(paymenttype='Credit')&Q(balancetype='Metal'))).values('gbal')
    cbal=invoices.annotate(cbal=Sum('balance',filter=Q(paymenttype='Credit')&Q(balancetype='Cash'))).values('cbal')
    balance=Customer.objects.annotate(gbal=Subquery(gbal),grec=Subquery(grec),gold=F('gbal')-F('grec'),cbal=Subquery(cbal),crec=Subquery(crec),cash=F('cbal')-F('crec'))


    context={'balance':balance}
    return render(request,'purchase/balance_list.html',context)

class InvoiceListView(ExportMixin,SingleTableMixin,FilterView):
    model = Invoice
    table_class = InvoiceTable
    filterset_class = InvoiceFilter
    template_name = 'purchase/invoice_list.html'
    paginate_by = 25

from product.models import Stree
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
        items = invoiceitem_form.save()
        # 2 problems
        # cant return unique item purchase :
        #   temp sol:merge with lot and return
        #       problem:cant delete this purchase
        #           (usually after splitting no one deletes purchase)

        for item in items:

            node,created = Stree.objects.get_or_create(name='Stock')
            node = node.traverse_to(item.product)

            if item.is_return:

                # tldr:never return unique item in purchase ,merge and then return from lot
                # cant create purchase invoice with unique product as being returned,
                # becoz it will create negative unique item
                # in case you want to return merge unique to lot and return
                # other way around is to find and delete unique return item baseed on weight here
                # and create again when this purchase is deleted and signals activated
                if node.tracking_type == 'Unique':
                    print("you need to merge a unique to lot to be able to return ")
                    continue

                node.weight -= item.weight
                node.quantity -= item.quantity
                node.save()
                node.update_status()

                return_node = Stree.objects.get(name='Return')
                return_node = return_node.traverse_parellel_to(node)
                return_node.weight +=item.weight
                return_node.quantity +=item.quantity
                return_node.save()
            else:
                if node.tracking_type == 'Unique':
                    print("node is unique")
                    node = Stree.objects.create(parent = node,tracking_type='Unique',cost=item.touch)
                node.weight +=item.weight
                node.quantity +=item.quantity

                node.cost = item.touch
                n = node.get_family()
                node.full_name = n[2].name + ' ' + node.name
                node.barcode = 'je'+str(node.id)
                node.save()
                node.update_status()

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
        paymentline_form = PaymentLineFormSet()

        return self.render_to_response(
            self.get_context_data(form=form,
                                  paymentline_form=paymentline_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        paymentline_form = PaymentLineFormSet(self.request.POST)
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

        remaining=amount-invpaid
        while remaining>0 :
            try:
                invtopay = Invoice.objects.filter(supplier=self.object.supplier,balancetype=self.object.type).exclude(status="Paid").order_by('created')[0]
            except IndexError:
                invtopay = None
            if invtopay !=None :
                if remaining >= invtopay.get_balance() :
                    remaining -= invtopay.get_balance()
                    PaymentLine.objects.create(payment=self.object,invoice=invtopay,amount=invtopay.get_balance())
                    invtopay.status="Paid"
                else :
                    PaymentLine.objects.create(payment=self.object,invoice=invtopay,amount=remaining)
                    invtopay.status="PartiallyPaid"
                    remaining=0
                invtopay.save()

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

class PaymentDeleteView(DeleteView):
    model = Payment
    success_url = reverse_lazy('purchase_payment_list')

class PaymentLineCreateView(CreateView):
    model = PaymentLine
    form_class = PaymentLineForm

class PaymentLineDeleteView(DeleteView):
    model = PaymentLine
    success_url = reverse_lazy('purchase_paymentline_list')
