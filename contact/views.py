from django.views.generic import DetailView
from django_tables2.views import SingleTableMixin
from django_tables2.export.views import ExportMixin
from .tables import CustomerTable
from django_filters.views import FilterView
from .filters import CustomerFilter
from .models import Customer
from .forms import CustomerForm
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from sales.models import Month
from django.db.models import  Sum,Q,Count
from datetime import datetime, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods  # new
from django.urls import reverse
from django.contrib import messages

@login_required
def home(request):
    data = dict()
    c=Customer.objects
    data['retailcount']=c.filter(type='Re').count()

    data['wol']=c.filter(type='Re',loan=None).count()
    data['wl']=data['retailcount']-data['wol']
    data['customercount']=c.all().count()

    data['whcount']=c.filter(type="Wh").count()
    data['withph'] = round((c.exclude(phonenumber = '911').count()/c.count())*100,2)
    data['religionwise']= c.values('religion').annotate(Count('religion')).order_by('religion')

    return render(request,'contact/home.html',context={'data':data},)

class CustomerListFilterView(SingleTableMixin, FilterView):
    filterset_class = CustomerFilter
    table_class = CustomerTable
    template_name = 'table1.html'
    paginate_by = 25

    
class CustomerListView(LoginRequiredMixin,ExportMixin,SingleTableMixin,FilterView):
    table_class = CustomerTable
    model = Customer
    template_name = 'contact/customer_list.html'
    filterset_class = CustomerFilter
    paginate_by =10

    def get(self, request, *args, **kwargs):
        if request.META.get('HTTP_HX_REQUEST'):
            self.template_name = 'contact/partials/customer_list_view.html'
        return super().get(request, *args, **kwargs)

@require_http_methods(['POST'])
def delete_customer(request, pk):
    Customer.objects.filter(id=pk).delete()
    return HttpResponse("")

@login_required
def create_customer(request):

    if request.method == 'POST':
   
        form = CustomerForm(request.POST or None)
        if form.is_valid():
            f = form.save(commit = False)
            f.created_by = request.user
            f.save()
            messages.success(request, f"created customer {f}")
            table = CustomerTable(data = Customer.objects.all())
            table.paginate(page=request.GET.get("page", 1), per_page=10)
            context = {'filter':CustomerFilter,'table': table}
            return render(request, 'contact/partials/customer_list_view.html', context)
        else:
            messages.error(request, f"Error creating customer")
            return render(request, 'form.html', {'form': form})

    else:
        form = CustomerForm()
        if request.META.get('HTTP_HX_REQUEST'):
            return render(request,'form.html',{'form':form})

        return render(request, 'contact/customer_form.html', {'form': form})
    

def reallot_receipts(request,pk):
    customer = Customer.objects.get(pk = pk)
    customer.reallot_receipts()
    return redirect(customer.get_absolute_url())

def reallot_payments(request, pk):
    customer = Customer.objects.get(pk=pk)
    customer.reallot_payments()
    return redirect(customer.get_absolute_url())
    
class CustomerDetailView(LoginRequiredMixin,DetailView):
    model = Customer
    
    def get(self, request, *args, **kwargs):
        if request.META.get('HTTP_HX_REQUEST'):
            self.template_name = 'contact/partials/detail.html'
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        data=self.object.sales.all()
        inv =data.exclude(status="Paid")
        how_many_days = 30
        context['current'] = inv.filter(created__gte = datetime.now()-timedelta(days=how_many_days)).aggregate(tc = Sum('balance',filter = Q(balancetype='Cash')),tm = Sum('balance',filter = Q(balancetype = 'Gold')))
        context['past'] = inv.filter(created__lte = datetime.now()-timedelta(days=how_many_days)).aggregate(tc = Sum('balance',filter = Q(balancetype='Cash')),tm = Sum('balance',filter = Q(balancetype = 'Gold')))
        context['monthwise'] = inv.annotate(month = Month('created')).values('month').order_by('month').annotate(tc = Sum('balance',filter = Q(balancetype='Cash')),tm = Sum('balance',filter = Q(balancetype = 'Gold'))).values('month','tm','tc')
        context['monthwiserev'] = data.annotate(month = Month('created')).values('month').order_by('month').annotate(tc = Sum('balance',filter = Q(balancetype='Cash')),tm = Sum('balance',filter = Q(balancetype = 'Gold'))).values('month','tm','tc')
        return context

def edit_customer(request,pk):
    customer = get_object_or_404(Customer,pk=pk)
    form = CustomerForm(request.POST or None,instance = customer)
    
    if form.is_valid():
        f = form.save(commit = False)
        f.created_by = request.user
        f.save()
        messages.success(request, f"updated customer {f}")
        return redirect(f.get_absolute_url())
    
    return render(request,'contact/customer_form.html',{'form':form,'customer':customer})



