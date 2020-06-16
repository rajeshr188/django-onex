from django.shortcuts import render
from girvi.models import Loan,Release
from sales.models import Invoice as salesinvoice,Receipt
from purchase.models import Invoice as purchaseinvoice,Payment
from django.db.models import Avg,Count,Sum
import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
# Create your views here.
@login_required
def daybook(request):

    q = request.GET.get('q', '')
    if q != '' :
        today =datetime.datetime.strptime(q, "%d%m%Y").date()
    else:
        today=datetime.date.today()

    loan = dict()
    loans = Loan.objects.filter(created__year=today.year,created__month=today.month,created__day=today.day).values('loanid','loanamount')
    loan['loans']= loans
    loan['total'] = loans.aggregate(t=Sum('loanamount'))

    release = dict()
    releases = Release.objects.filter(created__year=today.year,created__month=today.month,created__day=today.day).values('releaseid','loan__loanamount','interestpaid')
    release['releases']=releases
    release['total']=releases.aggregate(t=Sum('interestpaid'))
    release['releaseamount']=releases.aggregate(t=Sum('loan__loanamount'))

    sale=salesinvoice.objects.filter(created__year=today.year,created__month=today.month,created__day=today.day).values('balance')
    purchase=purchaseinvoice.objects.filter(created__year=today.year,created__month=today.month,created__day=today.day).values('balance')

    creditsale=dict()
    creditsalesinv=sale.filter(paymenttype="Credit")
    creditsale['metal']=creditsalesinv.filter(balancetype="Metal").aggregate(t=Sum('balance'))
    creditsale['cash']=creditsalesinv.filter(balancetype="Cash").aggregate(t=Sum('balance'))

    cashsale=dict()
    cashsalesinv=sale.filter(paymenttype="Cash")
    cashsale['metal']=cashsalesinv.filter(balancetype="Metal").aggregate(t=Sum('balance'))
    cashsale['cash']=cashsalesinv.filter(balancetype="Cash").aggregate(t=Sum('balance'))

    creditpur=dict()
    creditpurinv=purchase.filter(paymenttype="Credit")
    creditpur['metal']=creditpurinv.filter(balancetype="Metal").aggregate(t=Sum('balance'))
    creditpur['cash']=creditpurinv.filter(balancetype="Cash").aggregate(t=Sum('balance'))

    cashpur=dict()
    cashpurinv=purchase.filter(paymenttype="Cash")
    cashpur['metal']=cashpurinv.filter(balancetype="Metal").aggregate(t=Sum('balance'))
    creditpur['cash']=cashpurinv.filter(balancetype="Cash").aggregate(t=Sum('balance'))

    receipt=dict()
    rec=Receipt.objects.filter(created__year=today.year,created__month=today.month,created__day=today.day).values('type','total')
    receipt['cash']=rec.filter(type="Cash")
    receipt['cashtotal']=receipt['cash'].aggregate(t=Sum('total'))
    receipt['metal']=rec.filter(type="Metal")
    receipt['metaltotal']=receipt['metal'].aggregate(t=Sum('total'))

    payment=dict()
    pay=Payment.objects.filter(created__year=today.year,created__month=today.month,created__day=today.day).values('type','total')
    payment['cash']=pay.filter(type="Cash").aggregate(t=Sum('total'))
    payment['metal']=pay.filter(type="Metal").aggregate(t=Sum('total'))

    daybook=dict()
    daybook['date']=today
    daybook['creditsale']=creditsale
    daybook['cashsale']=cashsale
    daybook['creditpur']=creditpur
    daybook['cashpur']=cashpur
    daybook['receipt']=receipt
    daybook['payment']=payment
    daybook['loan']=loan
    daybook['release']=release

    context={'daybook':daybook}
    return render(request,'daybook/daybook.html',context)
