from typing import List

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django_tables2.config import RequestConfig
from num2words import num2words
from render_block import render_block_to_string

from contact.models import Customer
from product.models import PricingTier, PricingTierProductPrice, ProductVariant

from ..filters import PurchaseFilter
from ..forms import PurchaseForm, PurchaseItemForm
from ..models import Purchase, PurchaseItem
from ..tables import PurchaseTable


@login_required
def purchase_list(request):
    filter = PurchaseFilter(
        request.GET, queryset=Purchase.objects.all().select_related("supplier", "term")
    )
    table = PurchaseTable(filter.qs)
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
    form = PurchaseForm(request.POST or None)
    context = {"form": form}
    if form.is_valid():
        obj = form.save()
        if request.htmx:
            headers = {"HX-Redirect": obj.get_absolute_url()}
            return HttpResponse("Created", headers=headers)
        return redirect("purchase_invoice_list")
    return render(request, "sales/create_update.html", context)


# trigger signals to reallot if any payments since the invoice is updated
@login_required
def purchase_update(request, id=None):
    obj = get_object_or_404(Purchase, pk=id)

    form = PurchaseForm(request.POST or None, instance=obj)
    new_item_url = reverse(
        "purchase:purchase_invoiceitem_create", kwargs={"parent_id": obj.id}
    )
    context = {"object": obj, "form": form, "new_item_url": new_item_url}
    if form.is_valid():
        form.save()
        context["message"] = "Updated"
    if request.htmx:
        return render(request, "sales/partials/forms.html", context)
    return render(request, "sales/create_update.html", context)


@login_required
def purchase_detail_view(request, pk=None):
    obj = Purchase.objects.get(pk=pk)
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
    obj = Purchase.objects.get(id=id)
    if request.method == "POST":
        obj.delete()
        success_url = reverse("purchase:purchase_invoice_list")
        if request.htmx:
            headers = {"HX-Redirect": success_url}
            return HttpResponse("Success", headers=headers)
        return redirect(success_url)

    return render(request, "purchase/invoice_confirm_delete.html", {"object": obj})


@login_required
def purchase_ratecut_change(request, id):
    obj = Purchase.objects.get(pk=id)
    print(f"purchase_ratecut_change: {obj}")
    print(f"purchase_ratecut_change: {obj.is_ratecut}")
    if request.method == "POST":
        obj.is_ratecut = not obj.is_ratecut
        obj.save()
        print(f"purchase_ratecut_changed: {obj.is_ratecut}")
        for i in obj.purchase_items.all():
            i.save()
        success_url = reverse("purchase:purchase_invoice_list")
        if request.htmx:
            headers = {"HX-Redirect": success_url}
            return HttpResponse("Success", headers=headers)
        return redirect(success_url)
    # this return is nonsense
    return render(request, "purchase/invoice_confirm_delete.html", {"object": obj})


@login_required
def purchase_gst_change(request, id):
    obj = Purchase.objects.get(pk=id)
    print(f"purchase_gst_change: {obj}")
    print(f"purchase_gst_change: {obj.is_gst}")
    if request.method == "POST":
        obj.is_gst = not obj.is_gst
        obj.save()
        print(f"purchase_gst_changed: {obj.is_gst}")
        for i in obj.purchase_items.all():
            i.save()
        success_url = reverse("purchase:purchase_invoice_list")
        if request.htmx:
            headers = {"HX-Redirect": success_url}
            return HttpResponse("Success", headers=headers)
        return redirect(success_url)
    # this return is nonsense
    return render(request, "purchase/invoice_confirm_delete.html", {"object": obj})


@login_required
def purchase_item_update_hx_view(request, parent_id=None, id=None):
    if not request.htmx:
        raise Http404
    try:
        parent_obj = Purchase.objects.get(id=parent_id)
    except:
        parent_obj = None
    if parent_obj is None:
        return HttpResponse("Not found.")
    instance = None
    if id is not None:
        try:
            instance = PurchaseItem.objects.get(invoice=parent_obj, id=id)
        except:
            instance = None
    form = PurchaseItemForm(request.POST or None, instance=instance)
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
        return render(request, "purchase/item-inline.html", context)
    return render(request, "purchase/item-form.html", context)


@login_required
def purchaseitem_detail(request, pk):
    obj = PurchaseItem.objects.get(pk=pk)
    context = {
        "object": obj,
    }
    return render(request, "purchase/item-inline.html", context)


@login_required
def purchase_item_delete_view(request, parent_id=None, id=None):
    try:
        obj = PurchaseItem.objects.get(
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
        success_url = reverse(
            "purchase:purchase_invoice_detail", kwargs={"pk": parent_id}
        )
        if request.htmx:
            return render(
                request, "sales/partials/item-inline-delete-response.html", {"id": id}
            )
        return redirect(success_url)
    context = {"object": obj}
    return render(request, "purchase/invoice_confirm_delete.html", context)


@login_required
# not done yet
def get_product_price(request):
    print(request.GET)
    product = ProductVariant.objects.get(id=request.GET.get("product", ""))
    contact = Customer.objects.get(id=request.GET.get("supplier", ""))

    # Traverse the pricing tier hierarchy to get the effective selling price for the customer and product
    pricing_tier = contact.pricing_tier
    purchase_price = 0
    while pricing_tier:
        pricing_tier_price = PricingTierProductPrice.objects.filter(
            pricing_tier=pricing_tier, product=product
        ).first()
        if pricing_tier_price:
            purchase_price = pricing_tier_price.purchase_price
            break
        else:
            pricing_tier = pricing_tier.parent

    # Fallback to individual price for customer and product
    # if not pricing_tier:
    #     price = Price.objects.filter(product=product, customer=customer).first()
    #     selling_price = price.selling_price if price else None

    form = PurchaseItemForm(initial={"touch": purchase_price})
    context = {
        "field": form["touch"],
    }
    return render(request, "girvi/partials/field.html", context)


def home(request):
    context = {}
    qs = Purchase.objects
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
#     invoices = Purchase.objects.posted().filter(
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
