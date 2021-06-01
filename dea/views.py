from typing import List
from django.db import transaction
from django.db.models.expressions import OuterRef, Subquery
from django.db.models.fields import DecimalField
from django.db.models.query_utils import subclasses
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import CreateView, ListView, DeleteView, DetailView
from django.shortcuts import render
from djmoney.models.fields import MoneyField
# Create your views here.
from .models import Account, AccountStatement, AccountTransaction, Journal, Ledger, LedgerStatement, LedgerTransaction
from .forms import AccountForm, AccountStatementForm, LedgerForm, LedgerStatementForm

from django.db.models import Sum,Q,Max,F
from django.db.models.functions import Coalesce
from dea.utils.currency import Balance
from moneyed import Money

def home(request):
    l = Ledger.objects.all().prefetch_related('ledgerstatements','credit_txns','debit_txns')
    ledger =[]
    for i in l:
        try:
            ls = l.ledgerstatements.latest()
            cb = ls.get_cb()
            since = ls.created
        except:
            ls = None
            cb = Balance()
            since = None
        
        c_bal = Balance(
            [Money(r['total'], r["amount_currency"]) for r in i.ctxns(since).values('amount_currency').annotate(total=Sum('amount'))])\
            if i.ctxns(since=since) else Balance()
        d_bal = Balance(
            [Money(r['total'], r["amount_currency"]) for r in i.dtxns(since).values('amount_currency').annotate(total=Sum('amount'))])\
            if i.dtxns(since=since) else Balance()

        bal = cb + d_bal - c_bal

        ledger.append([i,bal])

    # ls = LedgerStatement.objects.filter(pk__in = LedgerStatement.objects.order_by().values(
    #         'ledgerno').annotate(max_id = Max('id')).values('max_id')).select_related('ledgerno')

   
    # cr_lt = LedgerTransaction.objects.filter(ledgerno = OuterRef('pk')).order_by().values('ledgerno')
    # cr_usd = cr_lt.annotate(
    #     cr_usd=Coalesce(Sum('amount',filter=Q(amount_currency = 'USD')),0)).values('cr_usd')
    # cr_inr = cr_lt.annotate(cr_inr=Coalesce(Sum(
    #     'amount', filter=Q(amount_currency='INR')),0)).values('cr_inr')

    # dr_lt = LedgerTransaction.objects.filter(ledgerno_dr=OuterRef(
    #     'pk')).order_by().values('ledgerno_dr')
    # dr_usd = dr_lt.annotate(dr_usd=Coalesce(Sum(
    #     'amount', filter=Q(amount_currency='USD')),0)).values('dr_usd')
    # dr_inr = dr_lt.annotate(dr_inr=Coalesce(Sum(
    #     'amount', filter=Q(amount_currency='INR')),0)).values('dr_inr')

    # ledger_bal = Ledger.objects.values('name').annotate(
    #     cr_usd = Subquery(cr_usd),
    #     cr_inr=Subquery(cr_inr),dr_usd=Subquery(dr_usd),dr_inr=Subquery(dr_inr),
    #     bal_usd = Coalesce(F('cr_usd'),0) - Coalesce(F('dr_usd'),0),bal_inr = Coalesce(F('cr_inr'),0)-Coalesce(F('dr_inr'),0)
    # )
    context={}
    context['ledger']=ledger   
    # context['ledger_bal'] = ledger_bal
    a = Account.objects.filter(contact__type='Su')
                  
    # context['accounts'] = AccountStatement.objects.filter(
    #                 pk__in = AccountStatement.objects.order_by().values('AccountNo').annotate(max_id = Max('id')).values('max_id')).select_related("AccountNo","AccountNo__contact")
    context['accounts'] = a
    journal = Journal.objects.all().select_related('content_type')
    # jrnls = []
    # for i in journal:
    #     # txns = lt.filter(journal = i,)
    #     jrnls.append({
    #                     'object_id':i.object_id,
    #                     'id':i.id,'created':i.created,'desc':i.desc,
    #                     'app_label':i.content_type.app_label,'model':i.content_type.model,
    #                     'content_object':i.content_object,'url_string':i.get_url_string(),
    #                     'content_type':i.content_type,
    #                     # 'txns':txns
    #                     })
    context['journal'] = journal

    
    return render(request, 'dea/home.html', {'data': context})

def generalledger(request):
    context = {}
    context['lt'] = LedgerTransaction.objects.all().order_by('-created')
    return render(request,'dea/gl.html',{'data':context})

def daybook(request):
    try:
        latest_stmt = LedgerStatement.objects.latest()
    except:
        print("no ledger statements")

def set_ledger_ob(request, pk):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = LedgerStatementForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            form.save()
            return redirect('/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = LedgerStatementForm()

    return render(request, 'dea/set_ledger_ob.html', {'form': form})


def set_acc_ob(request, pk):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = AccountStatementForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            form.save()
            return redirect('/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = AccountStatementForm()

    return render(request, 'dea/set_acc_ob.html', {'form': form})

def audit_acc(request,pk):
    acc = get_object_or_404(Account,pk=pk)
    acc.audit()
    return redirect(acc)

@transaction.atomic()
def audit_ledger(request):
    ledgers = Ledger.objects.all()
    for l in ledgers:
        l.audit()
    return redirect("/dea")
    

class JournalListView(ListView):
    queryset = Journal.objects.all().select_related('content_object')

class JournalDetailView(DetailView):
    model = Journal

class AccountCreateView(CreateView):
    model = Account
    form_class = AccountForm

class AccountListView(ListView):
    queryset = Account.objects.all().select_related('entity','AccountType_Ext','contact')
    paginate_by = 10

class AccountDetailView(DetailView):
    model = Account

class AccountStatementCreateView(CreateView):
    model = Account
    form_class = AccountStatementForm

class AccountStatementListView(ListView):
    model = AccountStatement

class LedgerCreateView(CreateView):
    model = Ledger
    form_class = LedgerForm

class LedgerListView(ListView):
    model = Ledger

class LedgerDetailView(DetailView):
    model = Ledger

class LedgerStatementCreateView(CreateView):
    model = LedgerStatement
    form_class = LedgerStatementForm

class LedgerStatementListView(ListView):
    model = LedgerStatement

class LedgerTransactionListView(ListView):
    model=LedgerTransaction




    

