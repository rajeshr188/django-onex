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

from product.models import Stree,Attribute,AttributeValue
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

        path_to_take = ['product_type','Purity','Weight','Gender','Design','Length','Initial','tracking_type']
        for item in items:

            product_variant = item.product
            product_type = product_variant.product.product_type
            attr = {**product_variant.product.attributes,**product_variant.attributes}
            attr = {Attribute.objects.get(id = item[0]).name : AttributeValue.objects.get(id = item[1]).name for item in attr.items()}
            attr['product_type']= product_type.name
            attr = {i:attr[i]for i in path_to_take if i in attr}
            path = list(attr.values())

            node = Stree.objects.get(name='Gold')
            # traverse the path creating or traversing nodes
            for p in path:
                if p in [item.name for item in node.get_children()]:
                    node = Stree.objects.get(name=p,parent = node)
                else :
                    node = Stree.objects.create(name = p,parent = node)
            if item.is_return:
                node.weight -= item.weight
            else:
                node.weight +=item.weight
            node.cost = item.touch
            n = node.get_family()
            node.barcode = n[1].barcode+str(node.id)
            node.save()

            if attr['tracking_type'] == 'Unique':
                if item.is_return:
                    node.weight -= item.weight
                else:
                    node.weight +=item.weight
                node.weight -= item.weight
                node.save()
                newnode = Stree.objects.create(parent = node,weight=item.weight,cost=item.touch)
                family = newnode.get_family()
                newnode.barcode = family[1].barcode + str(newnode.id)
                newnode.save()
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
