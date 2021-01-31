from typing import List
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import CreateView, ListView, DeleteView, DetailView
from django.shortcuts import render
# Create your views here.
from .models import Account, AccountStatement, AccountTransaction, Journal, Ledger, LedgerStatement, LedgerTransaction
from .forms import AccountForm, AccountStatementForm, LedgerForm, LedgerStatementForm


def home(request):
    context = {}
    context['accounts'] = Account.objects.exclude(contact__type='Re').select_related('AccountType_Ext','contact').all()
    context['ledger'] = Ledger.objects.select_related('AccountType').all()
    context['journal'] = Journal.objects.select_related('content_type').all()
    return render(request, 'dea/home.html', {'data': context})

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

def audit_ledger(request,pk):
    ledger = get_object_or_404(Ledger,pk=pk)
    ledger.audit()
    return redirect(ledger)

def mock_pledge_loan(request, pk):
    acc = Account.objects.get(id=pk)
    acc.pledge_loan(6500)
    return redirect("/dea")


def mock_repay_loan(request, pk):
    acc = Account.objects.get(id=pk)
    acc.repay_loan(6500)
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
