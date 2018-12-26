from django.shortcuts import render
from sales.models import Invoice as salesinvoice,Receipt
from purchase.models import Invoice as purchaseinvoice,Payment
from django.db.models import Avg,Count,Sum
import datetime
# Create your views here.
def daybook(request):

    today=datetime.date.today()

    sale=salesinvoice.objects.filter(created__year=today.year,created__month=today.month,created__day=today.day)
    purchase=purchaseinvoice.objects.filter(created__year=today.year,created__month=today.month,created__day=today.day)

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
    rec=Receipt.objects.filter(created__year=today.year,created__month=today.month,created__day=today.day)
    receipt['cash']=rec.filter(type="Cash")
    receipt['cashtotal']=receipt['cash'].aggregate(t=Sum('total'))
    receipt['metal']=rec.filter(type="Metal")
    receipt['metaltotal']=receipt['metal'].aggregate(t=Sum('total'))

    payment=dict()
    pay=Payment.objects.filter(created__year=today.year,created__month=today.month,created__day=today.day)
    payment['cash']=pay.filter(type="Cash").aggregate(t=Sum('total'))
    payment['metal']=pay.filter(type="Metal").aggregate(t=Sum('total'))

    daybook=dict()
    daybook['creditsale']=creditsale
    daybook['cashsale']=cashsale
    daybook['creditpur']=creditpur
    daybook['cashpur']=cashpur
    daybook['receipt']=receipt
    daybook['payment']=payment

    context={'daybook':daybook}
    return render(request,'daybook/daybook.html',context)
