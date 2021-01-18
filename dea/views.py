from typing import List
from django.shortcuts import render, redirect
from django.views.generic import CreateView, ListView, DeleteView, DetailView
from django.shortcuts import render
# Create your views here.
from .models import Account, AccountStatement, Ledger, LedgerStatement
from .forms import AccountForm, AccountStatementForm, LedgerForm, LedgerStatementForm


def home(request):
    context = {}
    context['accounts'] = Account.objects.all()
    context['ledger'] = Ledger.objects.all()

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


def mock_pledge_loan(request, pk):
    acc = Account.objects.get(id=pk)
    acc.pledge_loan(6500)
    return redirect("/dea")


def mock_repay_loan(request, pk):
    acc = Account.objects.get(id=pk)
    acc.repay_loan(6500)
    return redirect("/dea")


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
