from django.views.generic import DetailView, ListView, UpdateView, CreateView,DeleteView
from .models import License, Loan, Release
from .forms import LicenseForm, LoanForm, ReleaseForm
from django.urls import reverse,reverse_lazy
from contact.models import Customer
from django_tables2 import RequestConfig
from django_tables2.views import SingleTableMixin
from django_tables2.export.views import ExportMixin
from .tables import LoanTable
from django_filters.views import FilterView
from .filters import LoanFilter
import re
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Avg,Count,Sum
from num2words import num2words
import math
def home(request):
    data = dict()

    customer=dict()
    c=Customer.objects
    customer['count']=c.count()
    customer['latest']=','.join(lat.name for lat in c.order_by('-created')[:5])

    license =dict()
    l=License.objects
    license['count']=l.count()
    license['licenses']=','.join(lic.name for lic in l.all())


    loan=dict()
    l=Loan.objects
    loan['count']=l.count()
    loan['latest']=','.join(lat.loanid for lat in l.order_by('-created')[:5])
    loan['amount']=l.aggregate(t=Sum('loanamount'))
    loan['amount_words']=num2words(loan['amount']['t'],lang='en_IN')
    loan['gold_amount']=l.filter(itemtype='Gold').aggregate(t=Sum('loanamount'))
    loan['gold_weight']=l.filter(itemtype='Gold').aggregate(t=Sum('itemweight'))
    loan['gavg']=math.ceil(loan['gold_amount']['t']/loan['gold_weight']['t'])
    loan['silver_amount']=l.filter(itemtype='Silver').aggregate(t=Sum('loanamount'))
    loan['silver_weight']=l.filter(itemtype='Silver').aggregate(t=Sum('itemweight'))
    loan['savg']=math.ceil(loan['silver_amount']['t']/loan['silver_weight']['t'])
    release=dict()
    r=Release.objects
    release['count']=r.count()

    data['customer']=customer
    data['license']=license
    data['loan']=loan
    data['release']=release
    return render(request,'girvi/home.html',context={'data':data},)

class LicenseListView(ListView):
    model = License

class LicenseCreateView(CreateView):
    model = License
    form_class = LicenseForm

class LicenseDetailView(DetailView):
    model = License

class LicenseUpdateView(UpdateView):
    model = License
    form_class = LicenseForm

class LicenseDeleteView(DeleteView):
    model=License
    success_url=reverse_lazy('girvi_license_list')

class LoanListView(ExportMixin,SingleTableMixin,FilterView):
    table_class=LoanTable
    # table_data=Loan.objects.all()
    model = Loan
    template_name='girvi/loan_list.html'
    filterset_class=LoanFilter
    paginate_by=50

def incloanid():
    last=Loan.objects.all().order_by('id').last()
    if not last:
        return '1'
    splitl=re.split('(\d+)',last.loanid)
    billno=splitl[0] + str(int(splitl[1])+1)
    return str(billno)

def ld():
    last=Loan.objects.all().order_by('id').last()
    if not last:
        return timezone.now
    return last.created

class LoanCreateView(CreateView):
    model = Loan
    form_class = LoanForm

    def get_initial(self):
        if self.kwargs:
            customer=Customer.objects.get(id=self.kwargs['pk'])
            # license=License.objects.get(id=2)
            return{
                'customer':customer,
                'loanid':incloanid,
                # 'license':license,
                'created':ld,
            }

class LoanDetailView(DetailView):
    model = Loan

class LoanUpdateView(UpdateView):
    model = Loan
    form_class = LoanForm

class LoanDeleteView(DeleteView):
    model=Loan
    success_url=reverse_lazy('girvi_loan_list')

class ReleaseListView(ListView):
    model = Release

class ReleaseCreateView(CreateView):
    model = Release
    form_class = ReleaseForm

    def get_initial(self):
        if self.kwargs:
            loan=Loan.objects.get(slug=self.kwargs['slug'])
            return{'loan':loan,'interestpaid':loan.interestdue,}

class ReleaseDetailView(DetailView):
    model = Release

class ReleaseUpdateView(UpdateView):
    model = Release
    form_class = ReleaseForm

class ReleaseDeleteView(DeleteView):
    model=Release
    success_url=reverse_lazy('girvi_release_list')
