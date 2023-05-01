import re
from typing import List

import pytz
import tablib
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django_tables2.config import RequestConfig
from openpyxl import load_workbook
from render_block import render_block_to_string

from contact.models import Customer
from product.models import (
    PricingTier,
    PricingTierProductPrice,
    ProductVariant,
    StockLot,
)

from ..admin import InvoiceResource, ReceiptResource
from ..filters import InvoiceFilter
from ..forms import InvoiceForm, InvoiceItemForm
from ..models import Invoice, InvoiceItem

# from ..render import Render
from ..tables import InvoiceTable


def home(request):
    context = {}
    qs = Invoice.objects

    total = dict()
    total["total"] = qs.total_with_ratecut()
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

    total["gst"] = qs.gst().total_with_ratecut()
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

    total["nongst"] = qs.non_gst().total_with_ratecut()
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
    return render(request, "sales/home.html", context)


def sales_list(request):
    filter = InvoiceFilter(
        request.GET,
        queryset=Invoice.objects.all()
        .select_related("customer", "term", "approval")
        .prefetch_related(),
    )
    table = InvoiceTable(filter.qs)
    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    context = {"filter": filter, "table": table}

    if request.htmx:
        response = render_block_to_string(
            "sales/invoice_list.html", "content", context, request
        )
        return HttpResponse(response)
    return render(request, "sales/invoice_list.html", context)


@login_required
def sales_detail_view(request, pk=None):
    hx_url = reverse("sales:hx-detail", kwargs={"pk": pk})
    context = {
        "hx_url": hx_url,
    }
    return render(request, "sales/invoice_detail.html", context)


@login_required
def sales_detail_hx_view(request, pk=None):
    if not request.htmx:
        raise Http404
    obj = get_object_or_404(Invoice, pk=pk)
    # try:
    #     obj = Invoice.objects.get(
    #         id=id,
    #     )

    # except:
    #     obj = None
    # if obj is None:
    #     return HttpResponse("Not found.")
    new_item_url = reverse(
        "sales:sales_invoiceitem_create", kwargs={"parent_id": obj.id}
    )
    context = {
        "object": obj,
        "previous": obj.get_previous(),
        "next": obj.get_next(),
        "new_item_url": new_item_url,
    }
    return render(request, "sales/partials/detail.html", context)


@login_required
def sales_delete_view(request, id=None):
    obj = get_object_or_404(Invoice, pk=id)
    # try:
    #     obj = Invoice.objects.get(id=id)
    # except:
    #     obj = None
    # if obj is None:
    #     if request.htmx:
    #         return HttpResponse("Not Found")
    #     raise Http404
    if request.method == "POST":
        obj.delete()
        success_url = reverse("sales:sales_invoice_list")
        if request.htmx:
            headers = {"HX-Redirect": success_url}
            return HttpResponse("Success", headers=headers)
        return redirect(success_url)
    context = {"object": obj}
    return render(request, "sales/invoice_confirm_delete.html", context)


@login_required
def sale_item_delete_view(request, parent_id=None, id=None):
    # try:
    #     obj = InvoiceItem.objects.get(
    #         invoice__id=parent_id,
    #         id=id,
    #     )
    # except:
    #     obj = None
    # if obj is None:
    #     if request.htmx:
    #         return HttpResponse("Not Found")
    #     raise Http404
    obj = get_object_or_404(InvoiceItem, id=id)
    if request.method == "POST":
        id = obj.id
        obj.delete()
        success_url = reverse("sales:hx-detail", kwargs={"pk": parent_id})
        if request.htmx:
            return render(
                request, "sales/partials/item-inline-delete-response.html", {"id": id}
            )
        return redirect(success_url)
    context = {"object": obj}
    return render(request, "sales/invoice_confirm_delete.html", context)


def sale_create_view(request):
    form = InvoiceForm(request.POST or None)
    context = {"form": form}

    if form.is_valid():
        obj = form.save()
        if request.htmx:
            headers = {"HX-Redirect": obj.get_absolute_url()}
            return HttpResponse("Created", headers=headers)
        return redirect(obj.get_absolute_url())

    return render(request, "sales/create_update.html", context)


@login_required
def sale_update_view(request, id=None):
    obj = get_object_or_404(Invoice, id=id)
    form = InvoiceForm(request.POST or None, instance=obj)
    new_item_url = reverse(
        "sales:sales_invoiceitem_create", kwargs={"parent_id": obj.id}
    )
    context = {"form": form, "object": obj, "new_item_url": new_item_url}
    if form.is_valid():
        form.save()
        context["message"] = "Data saved."
    if request.htmx:
        return render(request, "sales/partials/forms.html", context)
    return render(request, "sales/create_update.html", context)


@login_required
def sale_item_update_hx_view(request, parent_id=None, id=None):
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
    url = reverse("sales:sales_invoiceitem_create", kwargs={"parent_id": parent_obj.id})
    if instance:
        url = instance.get_hx_edit_url()
    context = {"url": url, "form": form, "object": instance}
    if form.is_valid():
        new_obj = form.save(commit=False)
        if instance is None:
            new_obj.invoice = parent_obj
        new_obj.save()
        context["object"] = new_obj
        return render(request, "sales/partials/item-inline.html", context)

    return render(request, "sales/partials/item-form.html", context)


@login_required
def saleitem_detail(request, pk):
    obj = get_object_or_404(InvoiceItem, pk=pk)
    context = {"object": obj}
    return render(request, "sales/partials/item-inline.html", context)


# from approval.models import Approval
# class InvoiceCreateView(CreateView):
#     model = Invoice
#     form_class = InvoiceForm
#     success_url = None

#     def get_context_data(self,*args,**kwargs):
#         data = super(InvoiceCreateView,self).get_context_data(*args,**kwargs)
#         if self.request.method == 'POST':
#             data['items'] = InvoiceItemFormSet(self.request.POST)
#         else:
#             data['items'] = InvoiceItemFormSet()
#             if 'approvalid' in self.request.GET:

#                 approval = Approval.objects.get(id=self.request.GET['approvalid'])
#                 approvallines = approval.items.filter(status='Pending').values()
#                 data['form'].fields["customer"].queryset = Customer.objects.filter(
#                     id=approval.contact.id)
#                 data['form'].fields["approval"].initial = approval

#                 for subform, da in zip(data['items'].forms, approvallines):
#                     da.pop('id')
#                     subform.initial = da
#         return data

#     def form_valid(self,form):
#         context = self.get_context_data()
#         items = context['items']
#         with transaction.atomic():
#             form.instance.created_by = self.request.user
#             self.object = form.save()
#             if items.is_valid():
#                 items.instance = self.object
#                 items.save()
#         return super(InvoiceCreateView, self).form_valid(form)

#     def get_success_url(self) -> str:
#         return reverse_lazy('sales_invoice_detail', kwargs={'pk': self.object.pk})


# def list_balance(request):

#     receipts=Receipt.objects.filter(customer=OuterRef('pk')).order_by().values('customer')
#     grec=receipts.annotate(grec=Sum('total',filter=Q(type='Gold'))).values('grec')
#     crec=receipts.annotate(crec=Sum('total',filter=Q(type='Cash'))).values('crec')

#     invoices=Invoice.objects.filter(customer=OuterRef('pk')).\
#                 order_by().values('customer')
#     gbal=invoices.annotate(gbal=Sum('balance',
#             filter=Q(balancetype='Gold'))).values('gbal')
#     cbal=invoices.annotate(cbal=Sum('balance',
#             filter=Q(balancetype='Cash'))).values('cbal')

#     balance=Customer.objects.filter(type='Wh').values('id','name').\
#                 annotate(gbal=Subquery(gbal),grec=Subquery(grec),gold=F('gbal')-F('grec'),
#                         cbal=Subquery(cbal),crec=Subquery(crec),cash=F('cbal')-F('crec')).\
#                         order_by('name')

#     balance_total = balance.aggregate(gbal_total = Coalesce(Sum(F('gbal')),0),
#                     grec_total = Coalesce(Sum(F('grec')),0),
#                     cbal_total = Coalesce(Sum(F('cbal')),0),
#                     crec_total = Coalesce(Sum(F('crec')),0))

#     balance_nett_gold = balance_total['gbal_total']  - balance_total['grec_total']
#     balance_nett_cash = balance_total['cbal_total']-balance_total['crec_total']

#     balance_by_month = Invoice.objects.annotate(month = Month('created')).\
#                         values('month').order_by('month').\
#                         annotate(tc = Sum('balance',filter = Q(balancetype='Cash')),tm = Sum('balance',filter = Q(balancetype = 'Metal')))

#     context={'balance':balance,'balance_total':balance_total,
#                 'balance_nett_gold':balance_nett_gold,
#                 'balance_nett_cash':balance_nett_cash,
#                 'balance_by_month':balance_by_month,

#     }
#     return render(request,'sales/balance_list.html',context)


@login_required
# not done yet
def get_sale_price(request):
    product = StockLot.objects.get(id=request.GET.get("product", "")).variant
    contact = Customer.objects.get(id=request.GET.get("contact", ""))

    # Traverse the pricing tier hierarchy to get the effective selling price for the customer and product
    pricing_tier = contact.pricing_tier
    selling_price = 0
    while pricing_tier:
        pricing_tier_price = PricingTierProductPrice.objects.filter(
            pricing_tier=pricing_tier, product=product
        ).first()
        if pricing_tier_price:
            selling_price = pricing_tier_price.selling_price
            break
        else:
            pricing_tier = pricing_tier.parent

    # Fallback to individual price for customer and product
    # if not pricing_tier:
    #     price = Price.objects.filter(product=product, customer=customer).first()
    #     selling_price = price.selling_price if price else None

    form = InvoiceItemForm(initial={"touch": selling_price})
    context = {
        "field": form["touch"],
    }
    return render(request, "girvi/partials/field.html", context)


def sales_count_by_month(request):
    # data = Invoice.objects.extra(select={'date': 'DATE(created)'},order_by=['date']).values('date').annotate(count_items=Count('id'))
    data = (
        Invoice.objects.annotate(month=Month("created"))
        .values("month")
        .order_by("month")
        .annotate(tc=Sum("balance", filter=Q(balancetype="Metal")))
    )
    return JsonResponse(list(data), safe=False)


def simple_upload(request):
    if request.method == "POST" and request.FILES["myfile"]:
        myfile = request.FILES["myfile"]
        # fs = FileSystemStorage()
        # filename = fs.save(myfile.name, myfile)
        # uploaded_file_url = fs.url(filename)
        wb = load_workbook(myfile, read_only=True)
        sheet = wb.active

        inv = tablib.Dataset(
            headers=[
                "id",
                "customer",
                "created",
                "description",
                "balancetype",
                "balance",
            ]
        )
        rec = tablib.Dataset(
            headers=[
                "id",
                "customer",
                "created",
                "description",
                "type",
                "total",
            ]
        )
        bal = tablib.Dataset(headers=["customer", "cash_balance", "metal_balance"])
        pname = None
        for row in sheet.rows:
            if row[0].value is not None and "Sundry Debtors" in row[0].value:
                pname = re.search(r"\)\s([^)]+)", row[0].value).group(1).strip()
            elif pname is not None and row[0].value is None:
                if row[1].value is not None:
                    date = pytz.utc.localize(row[1].value)
                    # id = re.search(r'\:\s([^)]+)', row[3].value).group(1).strip()
                    if row[4].value is not None:
                        inv_list = ["", pname, date, row[2].value, "Cash", row[4].value]
                        inv.append(inv_list)
                    if row[9].value is not None:
                        rec_list = ["", pname, date, row[2].value, "Cash", row[9].value]
                        rec.append(rec_list)
                    if row[22].value is not None:
                        inv_list = [
                            "",
                            pname,
                            date,
                            row[2].value,
                            "Gold",
                            row[22].value,
                        ]
                        inv.append(inv_list)
                    if row[24].value is not None:
                        rec_list = [
                            "",
                            pname,
                            date,
                            row[2].value,
                            "Gold",
                            row[24].value,
                        ]
                        rec.append(rec_list)
                elif row[1].value is None and (
                    row[4].value and row[16].value and row[26].value is not None
                ):
                    bal_list = [pname, row[16].value, row[26].value]
                    bal.append(bal_list)
        # print(bal.export('csv'))
        inv_r = InvoiceResource()
        rec_r = ReceiptResource()

        print("running  inv wet run")
        inv_result = inv_r.import_data(inv, dry_run=False)  # Test the data import
        print("running  rec wet run")
        rec_result = rec_r.import_data(rec, dry_run=False)
        print("succesfuly imported")
        # if not inv_result.has_errors():
        #     print("running wet")
        #     inv_r.import_data(inv, dry_run=False)  # Actually import now
        # else :
        #     print("error occured")
        # if not rec_result.has_errors():
        #     rec_r.import_data(dataset, dry_run=False)  # Actually import now

        return render(request, "sales/simpleupload.html")

    return render(request, "sales/simpleupload.html")
