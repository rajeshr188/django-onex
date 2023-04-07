from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, UpdateView
from django_filters.views import FilterView

from utils.htmx_utils import for_htmx

from ..filters import ProductVariantFilter
from ..forms import ProductVariantForm
from ..models import Product, ProductVariant


@login_required
@for_htmx(use_block="content")
def productvariant_list(request):
    variants = ProductVariant.objects.all()
    filter = ProductVariantFilter(request.GET, queryset=variants)
    return TemplateResponse(
        request, "product/productvariant_list.html", {"filter": filter}
    )


@login_required
@for_htmx(use_block="content")
def variant_create(request, pk):
    product = get_object_or_404(Product.objects.all(), pk=pk)
    variant = ProductVariant(product=product)
    form = ProductVariantForm(request.POST or None, instance=variant)
    if form.is_valid():
        form.save()
        return redirect("product_productvariant_detail", pk=variant.pk)
    ctx = {"form": form, "product": product, "variant": variant}
    return TemplateResponse(request, "product/productvariant_form.html", ctx)


@login_required
@for_htmx(use_block="content")
def productvariant_detail(request, pk):
    variant = get_object_or_404(ProductVariant.objects.all(), pk=pk)
    return TemplateResponse(
        request, "product/productvariant_detail.html", {"object": variant}
    )


@login_required
@for_htmx(use_block="content")
def productvariant_update(request, pk):
    variant = get_object_or_404(ProductVariant.objects.all(), pk=pk)
    form = ProductVariantForm(request.POST or None, instance=variant)
    if form.is_valid():
        form.save()
        return redirect("product_productvariant_detail", pk=variant.pk)
    ctx = {"form": form, "variant": variant}
    return TemplateResponse(request, "product/productvariant_form.html", ctx)


class ProductVariantDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductVariant
    success_url = reverse_lazy("product_productvariant_list")


# @login_required
# def productvariant_delete(request, pk):
#     variant = get_object_or_404(ProductVariant.objects.all(), pk=pk)
#     if request.method == "POST":
#         variant.delete()
#         return redirect("product_productvariant_list")
#     return TemplateResponse(request, "product/productvariant_delete.html", {"variant": variant}
