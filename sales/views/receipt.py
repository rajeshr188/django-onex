from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView
from django_tables2.export.views import ExportMixin
from django_tables2.views import SingleTableMixin
from num2words import num2words

from ..filters import ReceiptFilter
from ..forms import ReceiptForm, ReceiptItemFormSet, ReceiptLineForm
from ..models import Receipt, ReceiptLine
# from ..render import Render
from ..tables import ReceiptTable

# def print_receipt(request, pk):
#     receipt = Receipt.objects.get(id=pk)
#     params = {"receipt": receipt, "inwords": num2words(receipt.total, lang="en_IN")}
#     return Render.render("sales/receipt.html", params)


class ReceiptListView(ExportMixin, SingleTableMixin, FilterView):
    model = Receipt
    table_class = ReceiptTable
    filterset_class = ReceiptFilter
    template_name = "sales/receipt_list.html"
    paginate_by = 25


class ReceiptCreateView(CreateView):
    model = Receipt
    form_class = ReceiptForm

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        receiptitem_form = ReceiptItemFormSet()

        return self.render_to_response(
            self.get_context_data(form=form, receiptitem_form=receiptitem_form)
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        receiptitem_form = ReceiptItemFormSet(self.request.POST)
        if form.is_valid() and receiptitem_form.is_valid():
            return self.form_valid(form, receiptitem_form)
        else:
            return self.form_invalid(form, receiptitem_form)

    def form_valid(self, form, receiptitem_form):
        form.instance.created_by = self.request.user
        self.object = form.save()
        receiptitem_form.instance = self.object
        receiptitem_form.save()
        return redirect(self.get_success_url())

    def form_invalid(self, form, receiptitem_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(
            self.get_context_data(form=form, receiptline_form=receiptitem_form)
        )


@transaction.atomic()
def post_receipt(request, pk):
    rcpt = Receipt.objects.get(id=pk)
    rcpt.post()
    return redirect(rcpt)


@transaction.atomic()
def unpost_receipt(request, pk):
    rcpt = Receipt.objects.get(id=pk)
    rcpt.unpost()
    return redirect(rcpt)


class ReceiptDetailView(DetailView):
    model = Receipt


class ReceiptUpdateView(UpdateView):
    model = Receipt
    form_class = ReceiptForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        receiptitem_form = ReceiptItemFormSet(instance=self.object)

        return self.render_to_response(
            self.get_context_data(form=form, receiptitem_form=receiptitem_form)
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        receiptitem_form = ReceiptItemFormSet(self.request.POST, instance=self.object)
        if form.is_valid() and receiptitem_form.is_valid():
            return self.form_valid(form, receiptitem_form)
        else:
            return self.form_invalid(form, receiptitem_form)

    def form_valid(self, form, receiptitem_form):
        self.object = form.save()

        receiptitem_form.instance = self.object
        receiptitem_form.save()
        return redirect(self.get_success_url())

    def form_invalid(self, form, receiptitem_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(
            self.get_context_data(form=form, receiptitem_form=receiptitem_form)
        )


# create a function view on receipt list page  to reallot all receipts


class ReceiptDeleteView(DeleteView):
    model = Receipt
    success_url = reverse_lazy("sales_receipt_list")


class ReceiptLineCreateView(CreateView):
    model = ReceiptLine
    form_class = ReceiptLineForm


class ReceiptLineUpdateView(UpdateView):
    model = ReceiptLine
    form = ReceiptLineForm


class ReceiptLineDeleteView(DeleteView):
    model = ReceiptLine
    success_url = reverse_lazy("sales_receiptline_list")
