from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Case, F, IntegerField, Sum, Value, When, Window
from django.db.models.query_utils import subclasses
from django.shortcuts import HttpResponse, get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls.base import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView

from dea.utils.currency import Balance
from utils.htmx_utils import for_htmx

from .forms import (AccountForm, AccountStatementForm, LedgerForm,
                    LedgerStatementForm)
# Create your views here.
from .models import (Account, Accountbalance, AccountStatement, Journal,
                     Ledger, Ledgerbalance, LedgerStatement, LedgerTransaction)


def home(request):
    lb = Ledgerbalance.objects.all()

    context = {}
    balancesheet = {}
    balancesheet["assets"] = lb.filter(AccountType="Asset")
    # Get the balance sheet data
    # balancesheet = lb.balancesheet()

    balancesheet["equity"] = lb.filter(AccountType="Equity")
    ta = Balance()
    tl = Balance()
    ti = Balance()
    te = Balance()
    for i in lb:
        if i.AccountType == "Asset":
            ta = ta + (i.get_currbal())
        elif i.AccountType == "Liability":
            tl = tl + abs(i.get_currbal())
        elif i.AccountType == "Income":
            ti = ti + abs(i.get_currbal())
        elif i.AccountType == "Expense":
            te = te + abs(i.get_currbal())
    pnloss = {}
    pnloss["income"] = lb.filter(AccountType="Income")
    pnloss["expense"] = lb.filter(AccountType="Expense")
    context["ta"] = ta
    context["tl"] = tl
    context["ti"] = ti
    context["te"] = te
    balancesheet["liabilities"] = lb.filter(AccountType="Liability")
    context["pnloss"] = pnloss

    context["balancesheet"] = balancesheet
    context["ledger"] = lb

    # context['accounts'] = AccountStatement.objects.filter(
    #                 pk__in = AccountStatement.objects.order_by().values('AccountNo').annotate(max_id = Max('id')).values('max_id')).select_related("AccountNo","AccountNo__contact")
    # a = Account.objects.filter(contact__type='Su')
    context["accounts"] = []

    context["journal"] = []
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

    return render(request, "dea/home.html", {"data": context})


def generalledger(request):
    context = {}
    context["lt"] = LedgerTransaction.objects.all().order_by("-created")[:10]
    return render(request, "dea/gl.html", {"data": context})


def daybook(request):
    try:
        latest_stmt = LedgerStatement.objects.latest()
    except:
        print("no ledger statements")
    return HttpResponse(status=404)


def set_ledger_ob(request, pk):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = LedgerStatementForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            form.save()
            return redirect("/")

    # if a GET (or any other method) we'll create a blank form
    else:
        form = LedgerStatementForm()

    return render(request, "dea/set_ledger_ob.html", {"form": form})


def set_acc_ob(request, pk):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = AccountStatementForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            form.save()
            return redirect("/")

    # if a GET (or any other method) we'll create a blank form
    else:
        form = AccountStatementForm()

    return render(request, "dea/set_acc_ob.html", {"form": form})


@transaction.atomic()
def audit_acc(request, pk):
    acc = get_object_or_404(Account, pk=pk)
    acc.audit()
    return redirect(acc)


@transaction.atomic()
def audit_ledger(request):
    ledgers = Ledger.objects.all()
    for l in ledgers:
        l.audit()
    return redirect("/dea")


class JournalListView(ListView):
    queryset = Journal.objects.all().select_related("content_type")
    paginate_by = 10


class JournalDetailView(DetailView):
    model = Journal


class JournalDeleteView(DeleteView):
    model = Journal
    success_url = reverse_lazy("dea_journals_list")


class AccountCreateView(CreateView):
    model = Account
    form_class = AccountForm


class AccountListView(ListView):
    # queryset = Account.objects.all().select_related('entity','AccountType_Ext','contact')
    queryset = Accountbalance.objects.all()
    template_name = "dea/account_list.html"
    # paginate_by = 10


@login_required
@for_htmx(use_block="content")
def account_detail(request, pk=None):
    acc = get_object_or_404(Account, pk=pk)
    ct = {}

    if acc.accountstatements.exists():
        acc_stmt = acc.accountstatements.latest()
        ls_created = acc_stmt.created
        txns = acc.txns(since=ls_created)

    else:
        txns = acc.txns()
        acc_stmt = None

    ct["acc_stmt"] = acc_stmt
    # op_bal = Balance() if acc_stmt is None else acc_stmt.get_cb()
    txns = txns.annotate(
        credit_or_debit=Case(
            When(XactTypeCode__XactTypeCode="Cr", then=Value(1)),
            default=Value(-1),
            output_field=IntegerField(),
        ),
        running_total=Window(
            expression=Sum(F("amount") * F("credit_or_debit")),
            partition_by=F("amount_currency"),
            order_by="created",
        ),
    ).order_by("created")
    # running_bal = op_bal
    ct["raw"] = txns
    ct["last"] = txns.last()
    return TemplateResponse(
        request, "dea/account_detail.html", {"object": acc, "ct": ct}
    )


# class AccountDetailView(DetailView):
#     model = Account

#     def get_context_data(self, **kwargs):
#         ct = super().get_context_data(**kwargs)
#         acc = ct["object"]

#         if acc.accountstatements.exists():
#             acc_stmt = acc.accountstatements.latest()
#             ls_created = acc_stmt.created
#             txns = acc.txns(since=ls_created)

#         else:
#             txns = acc.txns()
#             acc_stmt = None

#         ct["acc_stmt"] = acc_stmt
#         # op_bal = Balance() if acc_stmt is None else acc_stmt.get_cb()
#         txns = txns.annotate(
#             credit_or_debit=Case(
#                 When(XactTypeCode__XactTypeCode="Cr", then=Value(1)),
#                 default=Value(-1),
#                 output_field=IntegerField(),
#             ),
#             running_total=Window(
#                 expression=Sum(F("amount") * F("credit_or_debit")),
#                 partition_by=F("amount_currency"),
#                 order_by="created",
#             ),
#         ).order_by("created")
#         # running_bal = op_bal
#         ct["raw"] = txns
#         ct["last"] = txns.last()
#         return ct


class AccountStatementCreateView(CreateView):
    model = Account
    form_class = AccountStatementForm


class AccountStatementListView(ListView):
    model = AccountStatement


class AccountStatementDeleteView(DeleteView):
    model = AccountStatement
    success_url = reverse_lazy("dea_account_list")


class LedgerCreateView(CreateView):
    model = Ledger
    form_class = LedgerForm


class LedgerListView(ListView):
    model = Ledger


# optimise n+1 queries
class LedgerDetailView(DetailView):
    model = Ledger

    def get_context_data(self, **kwargs):
        ct = super().get_context_data(**kwargs)
        ls_created = (
            ct["object"].ledgerstatements.latest().created
            if ct["object"].ledgerstatements.exists()
            else None
        )
        ct["dtxns"] = ct["object"].dtxns(since=ls_created)
        ct["ctxns"] = ct["object"].ctxns(since=ls_created)
        return ct


class LedgerStatementCreateView(CreateView):
    model = LedgerStatement
    form_class = LedgerStatementForm


class LedgerStatementListView(ListView):
    model = LedgerStatement


class LedgerTransactionListView(ListView):
    model = LedgerTransaction
