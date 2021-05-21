from sea.models import Transaction
from django.shortcuts import render
from django.db.models import Sum,Q
# Create your views here.
def create_acc(request):
    pass

def acc_summary(request):
    data = {}
    opbal = Transaction.objects.filter(account__name = 'Op-bal').order_by('date').first()
    data['clbal_date'] = Transaction.objects.order_by('date').last()
    txns = Transaction.objects.exclude(account__name = 'Op-bal')
    bal_by_Acc = txns.values('account__name').annotate(cr=Sum('amount', filter=Q(txn_type='Cr')),
                                dr=Sum('amount', filter=Q(txn_type='Dr'))
                                )
    bal = txns.aggregate(cr = Sum('amount',filter = Q(txn_type = 'Cr')),
                            dr = Sum('amount',filter = Q(txn_type ='Dr'))
                                )
    clbal = (opbal.amount + bal['cr']) - bal['dr']
    data['opbal'] = opbal
    data['bal_by_acc'] = bal_by_Acc
    data['cr_bal'] = bal['cr']
    data['dr_bal'] = bal['dr']
    data['clbal'] = clbal
    return render(request,'sea/acc_summary.html',context ={'data':data},)

def statements(request):
    data={}
    return render(request,'',context ={'data':data})

def daywise_stat():
    pass
def monthwise_stat():
    pass
def yearwise_stat():
    pass
def check_ob(request):
    pass