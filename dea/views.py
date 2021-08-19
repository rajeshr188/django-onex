from typing import List
from django.db import transaction
from django.db.models.expressions import OuterRef, Subquery
from django.db.models.fields import DecimalField
from django.db.models.query import Prefetch
from django.db.models.query_utils import subclasses
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import CreateView, ListView, DeleteView, DetailView
from django.shortcuts import render
from djmoney.models.fields import MoneyField
# Create your views here.
from .models import Account, AccountStatement, AccountTransaction, Journal, Ledger, LedgerStatement, LedgerTransaction,Ledgerbalance
from .forms import AccountForm, AccountStatementForm, LedgerForm, LedgerStatementForm

from django.db.models import Sum,Q,Max,F
from django.db.models.functions import Coalesce
from dea.utils.currency import Balance
from moneyed import Money

def home(request):
    lb = Ledgerbalance.objects.all()
      
    context={}
    context['ledger']=lb   
                      
    # context['accounts'] = AccountStatement.objects.filter(
    #                 pk__in = AccountStatement.objects.order_by().values('AccountNo').annotate(max_id = Max('id')).values('max_id')).select_related("AccountNo","AccountNo__contact")
    # a = Account.objects.filter(contact__type='Su')
    context['accounts'] = []
    # journal = Journal.objects.all().select_related('content_type')
    context['journal'] = []
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


@transaction.atomic()
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
    queryset = Journal.objects.all().select_related('content_type')

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

    def get_context_data(self, **kwargs):
        ct = super().get_context_data(**kwargs)
        
        if ct['object'].accountstatements.exists():
            ls_created = ct['object'].accountstatements.latest().created
            ct['txns'] = ct['object'].txns(since=ls_created)
        else:
            ct['txns'] = ct['object'].txns()
        
        return ct

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

    def get_context_data(self, **kwargs) :
        ct = super().get_context_data(**kwargs)
        ls_created = ct['object'].ledgerstatements.latest().created
        ct['dtxns']= ct['object'].dtxns(since=ls_created)
        ct['ctxns']= ct['object'].ctxns(since = ls_created)
        return ct

class LedgerStatementCreateView(CreateView):
    model = LedgerStatement
    form_class = LedgerStatementForm

class LedgerStatementListView(ListView):
    model = LedgerStatement

class LedgerTransactionListView(ListView):
    model=LedgerTransaction




    

