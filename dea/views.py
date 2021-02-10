from typing import List
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import CreateView, ListView, DeleteView, DetailView
from django.shortcuts import render
# Create your views here.
from .models import Account, AccountStatement, AccountTransaction, Journal, Ledger, LedgerStatement, LedgerTransaction
from .forms import AccountForm, AccountStatementForm, LedgerForm, LedgerStatementForm

from django.db.models import Sum
from dea.utils.currency import Balance
from moneyed import Money
def home(request):
    
    ledger_txns = LedgerTransaction.objects.select_related('ledgerno','ledgerno_dr','journal').all()
    context = {}
    l=[]
    ledger_qs = Ledger.objects.all()
    for i in ledger_qs:
        latest_ls = i.get_latest_stmt()
        if latest_ls is None:
            since = None
            cb = Balance()
        else:
            since = latest_ls.created
            cb = latest_ls.get_cb()
        latest_ctxns = i.ctxns(since = since).filter(ledgerno = i)\
                                .values('amount_currency')\
                                .annotate(total = Sum('amount'))
        lct = Balance(
            [Money(r['total'],r['amount_currency']) for r in latest_ctxns]
        )
        latest_dtxns = i.dtxns(since = since).filter(ledgerno_dr = i)\
                                .values('amount_currency')\
                                .annotate(total=Sum('amount'))
        ldt = Balance(
            [Money(r['total'], r['amount_currency']) for r in latest_dtxns]
        )
        current_bal = cb + lct - ldt
        l.append({'ledger':i,'cb':current_bal})

    context['ledger']= l
    
    context['accounts'] = Account.objects.exclude(contact__type='Re').select_related('AccountType_Ext','contact').all()
    journal = Journal.objects.all()
    jrnls = []
    for i in journal:
        txns = ledger_txns.filter(journal = i,)
        jrnls.append({
                        'object_id':i.object_id,
                        'id':i.id,'created':i.created,'desc':i.desc,
                        'app_label':i.content_type.app_label,'model':i.content_type.model,
                        'content_object':i.content_object,'url_string':i.get_url_string(),
                        'content_type':i.content_type,'txns':txns})
    context['journal'] = jrnls
    
    return render(request, 'dea/home.html', {'data': context})

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
    model = Journal

class AccountCreateView(CreateView):
    model = Account
    form_class = AccountForm


class AccountListView(ListView):
    model = Account


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
