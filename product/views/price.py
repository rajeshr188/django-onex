from django.shortcuts import get_object_or_404, redirect, render

from ..forms import PricingTierForm, PricingTierProductPriceForm
from ..models import PricingTier, PricingTierProductPrice


def pricing_tier_list(request):
    context = {}
    object_list = PricingTier.objects.all()
    context["object_list"] = object_list
    return render(request, "product/price/pricingtier_list.html", context=context)


def pricing_tier_detail(request, pk):
    pricing_tier = get_object_or_404(PricingTier, id=pk)
    return render(
        request, "product/price/pricingtier_detail.html", context={"obj": pricing_tier}
    )


def pricing_tier_create(request):
    form = PricingTierForm(request or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return
    render(request, "", context={"form": form})


def pricing_tier_update(request):
    form = PricingTierForm(request or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return
    render(request, "", context={"form": form})


def pricing_tier_delete(request, pk):
    obj = get_object_or_404(PricingTier, id=pk)
    obj.delete()
    return HttpResponse(status=201)


def pricing_tier_product_price_create(request):
    form = PricingTierForm(request or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return
    render(request, "", context={"form": form})


def pricing_tier_product_price_update(request):
    form = PricingTierForm(request or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return
    render(request, "", context={"form": form})


def pricing_tier_product_price_delete(request, pk):
    obj = get_object_or_404(PricingTierProductPrice, id=pk)
    obj.delete()
    return HttpResponse(status=201)
