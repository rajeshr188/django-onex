from django.views.generic import DetailView, ListView, UpdateView, CreateView,DeleteView
from django_tables2 import RequestConfig
from django_tables2.views import SingleTableMixin
from django_tables2.export.views import ExportMixin
from .tables import CustomerTable,SupplierTable
from django_filters.views import FilterView
from .filters import CustomerFilter,SupplierFilter
from .models import Customer, Supplier
from .forms import CustomerForm, SupplierForm
from django.urls import reverse,reverse_lazy
from girvi.models import Loan
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from sales.models import Invoice,Month
from django.db.models import  Sum,Q,F,OuterRef,Subquery,Count
from datetime import datetime, timedelta,date
from sales.tables import InvoiceTable
def home(request):
    data = dict()
    data['customercount']=str(Customer.objects.count())
    data['suppliercount']=Customer.objects.count()
    return render(request,'contact/home.html',context={'data':data},)

class CustomerListView(ExportMixin,SingleTableMixin,FilterView):
    table_class = CustomerTable
    model = Customer
    template_name = 'contact/customer_list.html'
    filterset_class = CustomerFilter
    paginate_by = 25

class CustomerCreateView(CreateView):
    model = Customer
    form_class = CustomerForm
    success_url=reverse_lazy('contact_customer_list')


class CustomerDetailView(DetailView):
    model = Customer
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        data=self.object.invoicee.all()
        table = InvoiceTable(data,exclude=('customer','edit','delete',))
        table.paginate(page=self.request.GET.get('page', 1), per_page=25)
        context['invoices']=table
        inv = Invoice.objects.filter(customer=self.object.id).exclude(status="Paid")
        how_many_days = 30
        context['current'] = inv.filter(created__gte = datetime.now()-timedelta(days=how_many_days)).aggregate(tc = Sum('balance',filter = Q(balancetype='Cash')),tm = Sum('balance',filter = Q(balancetype = 'Metal')))
        context['past'] = inv.filter(created__lte = datetime.now()-timedelta(days=how_many_days)).aggregate(tc = Sum('balance',filter = Q(balancetype='Cash')),tm = Sum('balance',filter = Q(balancetype = 'Metal')))
        context['monthwise'] = inv.annotate(month = Month('created')).values('month').order_by('month').annotate(tc = Sum('balance',filter = Q(balancetype='Cash')),tm = Sum('balance',filter = Q(balancetype = 'Metal'))).values('month','tm','tc')
        return context

class CustomerUpdateView(UpdateView):
    model = Customer
    form_class = CustomerForm

class CustomerDelete(DeleteView):
    model=Customer
    success_url = reverse_lazy('contact_customer_list')

class SupplierListView(ExportMixin,SingleTableMixin,FilterView):
    table_class = SupplierTable
    model = Supplier
    template_name = 'contact/supplier_list.html'
    filterset_class = SupplierFilter
    paginate_by = 25

class SupplierCreateView(CreateView):
    model = Supplier
    form_class = SupplierForm

class SupplierDetailView(DetailView):
    model = Supplier

class SupplierUpdateView(UpdateView):
    model = Supplier
    form_class = SupplierForm

class SupplierDelete(DeleteView):
    model=Supplier
    success_url = reverse_lazy('contact_supplier_list')
