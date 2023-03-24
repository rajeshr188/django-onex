from typing import List

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django_filters.views import FilterView
from django_tables2.config import RequestConfig
from django_tables2.export.views import ExportMixin
from django_tables2.views import SingleTableMixin
from num2words import num2words
from render_block import render_block_to_string

from contact.models import Customer

from ..filters import InvoiceFilter
from ..forms import InvoiceForm, InvoiceItemForm
from ..models import Invoice, InvoiceItem

# from ..render import Render
from ..tables import InvoiceTable


@login_required
def purchase_list(request):
    filter = InvoiceFilter(
        request.GET, queryset=Invoice.objects.all().select_related('supplier','term')
    )
    table = InvoiceTable(filter.qs)
    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    context = {"filter": filter, "table": table}
    if request.htmx:
        response = render_block_to_string(
            "purchase/invoice_list.html", "content", context, request
        )
        return HttpResponse(response)
    else:
        return render(request, "purchase/invoice_list.html", context)


@login_required
def purchase_create(request):
    form = InvoiceForm(request.POST or None)
    context = {"form": form}
    if form.is_valid():
        obj = form.save()
        if request.htmx:
            headers = {"HX-Redirect": obj.get_absolute_url()}
            return HttpResponse("Created", headers=headers)
        return redirect("purchase_invoice_list")
    return render(request, "purchase/create_update.html", context)


@login_required
def purchase_update(request, id=None):
    obj = get_object_or_404(Invoice, pk=id)
    form = InvoiceForm(request.POST or None, instance=obj)
    new_item_url = reverse("purchase:purchase_invoiceitem_create", kwargs={"parent_id": obj.id})
    context = {"object": obj, "form": form, "new_item_url": new_item_url}
    if form.is_valid():
        form.save()
        context["message"] = "Updated"
    if request.htmx:
        return render(request, "shared/partials/forms.html", context)
    return render(request, "sales/create_update.html", context)


@login_required
def purchase_detail_view(request, id=None):
    obj = Invoice.objects.get(id=id)
    context = {
        "object": obj,
        "previous": obj.get_previous(),
        "next": obj.get_next(),
    }
    if request.htmx:
        return render("purchase/partials/detail.html", context)
    return render(request, "purchase/purchase_detail.html", context)


@login_required
def purchase_delete_view(request, id=None):
    obj = Invoice.objects.get(id=id)
    if request.method == "POST":
        obj.delete()
        success_url = reverse("purchase_invoice_list")
        if request.htmx:
            headers = {"HX-Redirect": success_url}
            return HttpResponse("Success", headers=headers)
        return redirect(success_url)
    return render(request, "purchase/invoice_confirm_delete.html", {"object": obj})


@login_required
def purchase_item_update_hx_view(request, parent_id=None, id=None):
    if not request.htmx:
        raise Http404
    try:
        parent_obj = Invoice.objects.get(id=parent_id)
    except:
        parent_obj = None
    if parent_obj is None:
        return HttpResponse("Not found.")
    instance = None
    if id is not None:
        try:
            instance = InvoiceItem.objects.get(invoice=parent_obj, id=id)
        except:
            instance = None
    form = InvoiceItemForm(request.POST or None, instance=instance)
    url = reverse(
        "purchase:purchase_invoiceitem_create", kwargs={"parent_id": parent_obj.id}
    )
    if instance:
        url = instance.get_hx_edit_url()
    context = {"url": url, "form": form, "object": instance}
    if form.is_valid():
        new_obj = form.save(commit=False)
        if instance is None:
            new_obj.invoice = parent_obj
        new_obj.save()
        context["object"] = new_obj
        return render(request, "purchase/partials/item-inline.html", context)
    return render(request, "purchase/partials/item-form.html", context)


@login_required
def purchase_item_delete_view(request, parent_id=None, id=None):
    try:
        obj = InvoiceItem.objects.get(
            invoice__id=parent_id,
            id=id,
        )
    except:
        obj = None
    if obj is None:
        if request.htmx:
            return HttpResponse("Not Found")
        raise Http404
    if request.method == "POST":
        id = obj.id
        obj.delete()
        success_url = reverse("purchase_invoice_detail", kwargs={"id": parent_id})
        if request.htmx:
            return render(
                request, "sales/partials/item-inline-delete-response.html", {"id": id}
            )
        return redirect(success_url)
    context = {"object": obj}
    return render(request, "purchase/invoice_confirm_delete.html", context)


def post_purchase(request, pk):
    # use get_objector404
    purchase_inv = Invoice.objects.get(id=pk)
    # post to dea & stock
    purchase_inv.post()
    return redirect(purchase_inv)


def unpost_purchase(request, pk):
    purchase_inv = Invoice.objects.get(id=pk)
    # unpost to dea & stock
    purchase_inv.unpost()
    return redirect(purchase_inv)


def home(request):
    context = {}
    qs = Invoice.objects
    qs_posted = qs.posted()

    total = dict()
    total["total"] = qs_posted.total_with_ratecut()
    if total["total"]["cash"]:
        total["total"]["gmap"] = round(
            total["total"]["cash_g"] / total["total"]["cash_g_nwt"], 3
        )
        total["total"]["smap"] = round(
            total["total"]["cash_s"] / total["total"]["cash_s_nwt"], 3
        )
    else:
        total["total"]["gmap"] = 0
        total["total"]["smap"] = 0

    total["gst"] = qs_posted.gst().total_with_ratecut()
    if total["gst"]["cash"]:
        total["gst"]["gmap"] = round(
            total["gst"]["cash_g"] / total["gst"]["cash_g_nwt"], 3
        )
        total["gst"]["smap"] = round(
            total["gst"]["cash_s"] / total["gst"]["cash_s_nwt"], 3
        )
    else:
        total["gst"]["gmap"] = 0
        total["gst"]["smap"] = 0

    total["nongst"] = qs_posted.non_gst().total_with_ratecut()
    if total["nongst"]["cash"]:
        total["nongst"]["gmap"] = round(
            total["nongst"]["cash_g"] / total["nongst"]["cash_g_nwt"], 3
        )
        total["nongst"]["smap"] = round(
            total["nongst"]["cash_s"] / total["nongst"]["cash_s_nwt"], 3
        )
    else:
        total["nongst"]["gmap"] = 0
        total["nongst"]["smap"] = 0

    context["total"] = total

    return render(request, "purchase/home.html", context)


# def print_invoice(pk):
#     invoice = Invoice.objects.get(id=pk)
#     params = {"invoice": invoice}
#     return Render.render("purchase/invoice_pdf.html", params)


# def list_balance(request):
#     acs = AccountStatement.objects.filter(AccountNo__contact = OuterRef('supplier')).order_by('-created')[:1]
#     acs_cb = AccountStatement.objects.filter(
#         AccountNo__contact=OuterRef('pk')).order_by('-created')[:1]
#     payments=Payment.objects.filter(
#         posted = True,
#         supplier=OuterRef('pk'),
#         created__gte = Subquery(acs.values('created'))
#         ).order_by().values('supplier')
#     grec=payments.annotate(grec=Sum('total',filter=Q(type='Gold'))).values('grec')
#     crec=payments.annotate(crec=Sum('total',filter=Q(type='Cash'))).values('crec')
#     invoices = Invoice.objects.posted().filter(
#         supplier=OuterRef('pk'),
#         created__gte=Subquery(acs.values('created'))
#         ).order_by().values('supplier')
#     gbal=invoices.annotate(gbal=Sum('balance',filter=Q(balancetype='Gold'))).values('gbal')
#     cbal=invoices.annotate(cbal=Sum('balance',filter=Q(balancetype='Cash'))).values('cbal')

#     balance=Customer.objects.filter(type="Su").annotate(
#                                     cb = Subquery(acs_cb.values('ClosingBalance')),
#                                     gbal=Subquery(gbal),grec=Subquery(grec),gold=F('gbal')-F('grec')
#                                     ,cbal=Subquery(cbal),crec=Subquery(crec),cash=F('cbal')-F('crec'))
#     context={'balance':balance}
#     return render(request,'purchase/balance_list.html',context)
