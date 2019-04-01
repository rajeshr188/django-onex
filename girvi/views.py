from django.views.generic import DetailView, ListView, UpdateView, CreateView,DeleteView
from django.views.generic.dates import YearArchiveView,MonthArchiveView,WeekArchiveView
from django.urls import reverse,reverse_lazy
import re
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Avg,Count,Sum,Q
from django.db.models.functions import Cast
from django.db.models.fields import DateField

from .models import License, Loan, Release,Month,Year
from .forms import LicenseForm, LoanForm, ReleaseForm,Release_formset
from .tables import LoanTable,ReleaseTable
from .filters import LoanFilter,ReleaseFilter
from contact.models import Customer

from django_tables2 import RequestConfig
from django_tables2.views import SingleTableMixin
from django_tables2.export.views import ExportMixin
from django_filters.views import FilterView

from num2words import num2words
import math
import datetime
from dateutil.relativedelta import relativedelta
from django.db.models import Subquery,OuterRef,Prefetch

def notice(request):
    qyr = request.GET.get('qyr',None)
    # qcust = request.GET.GET('qcust',None)
    if qyr is None:
        qyr=1
    print(type(qyr))
    a_yr_ago = timezone.now() - relativedelta(years=int(qyr))

    cust = Customer.objects.filter(type="Re",loan__created__lt=a_yr_ago,
                                        loan__release__isnull=True).\
                                        prefetch_related(Prefetch('loan_set',
                                                queryset = Loan.objects.filter(
                                                release__isnull=True,
                                                created__lt=a_yr_ago
                                                ))).annotate(
                                                t=Sum('loan__loanamount')
                                                )
    data = {}

    data['totalamount']=cust.aggregate(loancount = Count('loan'),t=Sum('loan__loanamount'))
    data['cust']=cust

    return render(request,'girvi/notice.html',context={'data':data})

def home(request):
    data = dict()
    today = datetime.date.today()
    customer=dict()
    c=Customer.objects
    customer['withoutloans']=c.annotate(num_loans=Count('loan')).filter(num_loans=0).count()
    # customer['withoutloans']=c.filter(loan__isnull=True).count()
    customer['withloans']=c.annotate(num_loans=Count('loan')).filter(num_loans__gt=0).count()
    customer['count']=c.count()
    customer['latest']=','.join(lat.name for lat in c.order_by('-created')[:5])
    customer['maxloans']=c.filter(loan__release__isnull=True).annotate(num_loans=Count('loan'),sum_loans=Sum('loan__loanamount')).values('name','num_loans','sum_loans').order_by('-num_loans')[:10]

    license =dict()
    l=License.objects
    license['count']=l.count()
    # license['licenses']=','.join(lic.name for lic in l.all())
    license['totalloans']=l.annotate(t=Sum('loan__loanamount'))
    licchart = l.annotate(la=Sum('loan__loanamount')).values('name','la')
    license['licchart']=list(licchart)

    loan=dict()
    l=Loan.unreleased
    loan['count']=l.count()
    loan['uniquecount']=l.annotate(c=Count('customer')).order_by('c')
    loan['latest']=','.join(lat.loanid for lat in l.order_by('-created')[:5])
    loan['amount']=l.aggregate(t=Sum('loanamount'))
    loan['amount_words']=num2words(loan['amount']['t'],lang='en_IN')
    loan['gold_amount']=l.filter(itemtype='Gold').aggregate(t=Sum('loanamount'))
    loan['gold_weight']=l.filter(itemtype='Gold').aggregate(t=Sum('itemweight'))
    loan['gavg']=math.ceil(loan['gold_amount']['t']/loan['gold_weight']['t'])
    loan['silver_amount']=l.filter(itemtype='Silver').aggregate(t=Sum('loanamount'))
    loan['silver_weight']=l.filter(itemtype='Silver').aggregate(t=Sum('itemweight'))
    loan['savg']=math.ceil(loan['silver_amount']['t']/loan['silver_weight']['t'])
    chart=(l.aggregate(gold=Sum('loanamount',filter=Q(itemtype="Gold")),silver=Sum('loanamount',filter=Q(itemtype="Silver")),bronze=Sum('loanamount',filter=Q(itemtype="Bronze"))))
    fixed = []
    fixed.append(chart['gold'])
    fixed.append(chart['silver'])
    fixed.append(chart['bronze'])
    loan['chart']=fixed
    datetimel = l.annotate(year=Year('created')).values('year').annotate(l = Sum('loanamount')).order_by('year').values_list('year','l',named=True)
    thismonth = l.filter(created__year = today.year,created__month = today.month).annotate(date_only=Cast('created', DateField()),t=Sum('loanamount')).order_by('created').values_list('date_only','t',named=True)
    # fixed = []
    # for row in datetime:
    #     fixed.append([row[0],row[1]])
    loan['datechart']=datetimel
    loan['thismonth']=thismonth
    release=dict()
    r=Release.objects
    release['count']=r.count()

    data['customer']=customer
    data['license']=license
    data['loan']=loan
    data['release']=release
    return render(request,'girvi/home.html',context={'data':data},)

class LoanYearArchiveView(YearArchiveView):
    queryset = Loan.objects.all()
    date_field = "created"
    make_object_list = True
    allow_future = True

class LoanMonthArchiveView(MonthArchiveView):
    queryset = Loan.objects.all()
    date_field = "created"
    allow_future = True

class LoanWeekArchiveView(WeekArchiveView):
    queryset = Loan.objects.all()
    date_field = "created"
    week_format = "%W"
    allow_future = True

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
    model = Loan
    template_name='girvi/loan_list.html'
    filterset_class=LoanFilter
    paginate_by=10

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
        # if self.kwargs:
        # customer=Customer.objects.get(id=self.kwargs['pk'])
        license=License.objects.get(id=2)
        return{
            # 'customer':customer,
            'loanid':incloanid,
            'license':license,
            # 'created':ld,
        }

class LoanDetailView(DetailView):
    model = Loan

class LoanUpdateView(UpdateView):
    model = Loan
    form_class = LoanForm

class LoanDeleteView(DeleteView):
    model=Loan
    success_url=reverse_lazy('girvi_loan_list')

class ReleaseListView(ExportMixin,SingleTableMixin,FilterView):
    table_class=ReleaseTable
    model = Release
    template_name='girvi/release_list.html'
    filterset_class=ReleaseFilter
    paginate_by=20

class ReleaseCreateView(CreateView):
    model = Release
    form_class = ReleaseForm

    def get_initial(self):
        if self.kwargs:
            loan=Loan.objects.get(id=self.kwargs['pk'])
            return{'loan':loan,'interestpaid':loan.interestdue,}

class ReleaseDetailView(DetailView):
    model = Release

class ReleaseUpdateView(UpdateView):
    model = Release
    form_class = ReleaseForm

class ReleaseDeleteView(DeleteView):
    model=Release
    success_url=reverse_lazy('girvi_release_list')
