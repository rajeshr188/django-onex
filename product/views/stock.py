from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from django.views.generic.base import TemplateView

from ..filters import StockFilter
from ..forms import (StockForm, StockTransactionForm, UniqueForm,
                     stockstatement_formset)
from ..models import Stock, StockLot, StockStatement, StockTransaction


@login_required
def split_lot(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == "POST":
        form = UniqueForm(request.POST or None)
        if form.is_valid():
            weight = form.cleaned_data["weight"]
            stock.split(weight)
            return reverse_lazy("product_stock_list")
    else:
        form = UniqueForm(initial={"stock": stock})
    context = {
        "form": form,
    }

    return render(request, "product/split_lot.html", context)


@login_required
def merge_lot(request, pk):
    node = Stock.objects.get(id=pk)
    print(f"to merge node{node}")
    node.merge()
    return reverse_lazy("product_stock_list")


@login_required
def stock_list(request):
    context = {}
    st = Stock.objects.all()
    stock_filter = StockFilter(request.GET, queryset=st)
    stock = []
    for i in stock_filter.qs:
        bal = {}
        try:
            ls = i.stockstatement_set.latest()
            cwt = ls.Closing_wt
            cqty = ls.Closing_qty
        except StockStatement.DoesNotExist:
            ls = None
            cwt = 0
            cqty = 0
        in_txns = i.stock_in_txns(ls)
        out_txns = i.stock_out_txns(ls)
        bal["wt"] = cwt + (in_txns["wt"] - out_txns["wt"])
        bal["qty"] = cqty + (in_txns["qty"] - out_txns["qty"])
        stock.append([i, bal])
    context["stock"] = stock
    return render(
        request, "product/stock_list.html", {"filter": stock_filter, "data": context}
    )


class StockCreateView(LoginRequiredMixin, CreateView):
    model = Stock
    form_class = StockForm


class StockUpdateView(LoginRequiredMixin, UpdateView):
    model = Stock
    form_class = StockForm


class StockDetailView(LoginRequiredMixin, DetailView):
    model = Stock


class StockLotDetailView(LoginRequiredMixin, DetailView):
    model = StockLot


class StockDeleteView(LoginRequiredMixin, DeleteView):
    model = Stock
    success_url = reverse_lazy("product_stock_list")


class StockTransactionCreateView(LoginRequiredMixin, CreateView):
    model = StockTransaction
    form_class = StockTransactionForm


class StockTransactionListView(LoginRequiredMixin, ListView):
    model = StockTransaction


class StockTransactionDetailView(LoginRequiredMixin, DetailView):
    model = StockTransaction


class StockTransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = StockTransaction
    form_class = StockTransactionForm


class StockTransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = StockTransaction
    success_url = reverse_lazy("product_stocktransaction_list")


class StockStatementListView(LoginRequiredMixin, ListView):
    model = StockStatement


class StockStatementView(TemplateView):
    template_name = "product/add_stockstatement.html"

    def get(self, *args, **kwargs):
        formset = stockstatement_formset(queryset=StockStatement.objects.none())
        return self.render_to_response({"stockstatement_formset": formset})

    def post(self, *args, **kwargs):
        formset = stockstatement_formset(data=self.request.POST)
        if formset.is_valid():
            formset.save()
            return redirect(reverse_lazy("stockstatement_list"))

        return self.render_to_response({"stockstatement_formset": formset})


@login_required
def audit_stock(request):
    stocks = Stock.objects.all()
    for i in stocks:
        i.audit()
    return reverse_lazy("product_stock_list")


from django.db.models import Q


def stock_select(request, q):
    objects = Stock.objects.filter(
        Q(variant__name__icontains=q) | Q(barcode__icontains=q) | Q(huid__contains=q)
    )
    return render(request, "product/stock_select.html", context={"result": objects})
