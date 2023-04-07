from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.views.generic import DeleteView
from utils.htmx_utils import for_htmx
from ..filters import ProductFilter
from ..forms import ProductForm, ProductVariantForm
from ..models import Product, ProductType, ProductVariant


# create product_list with filter view
@login_required
@for_htmx(use_block="content")
def product_list(request):
    products = Product.objects.prefetch_related("variants", "images").all()
    filter = ProductFilter(request.GET, queryset=products)
    return TemplateResponse(request, "product/product_list.html",{"filter": filter})

@login_required
@for_htmx(use_block="content")
def product_create(request, type_pk):
    track_inventory = True
    product_type = get_object_or_404(ProductType, pk=type_pk)
    create_variant = not product_type.has_variants
    product = Product()
    product.product_type = product_type
    product_form = ProductForm(request.POST or None, instance=product)
    if create_variant:
        variant = ProductVariant(product=product, track_inventory=track_inventory)
        variant_form = ProductVariantForm(
            request.POST or None, instance=variant, prefix="variant"
        )
        variant_errors = not variant_form.is_valid()
    else:
        variant_form = None
        variant_errors = False

    if product_form.is_valid() and not variant_errors:
        product = product_form.save()
        if create_variant:
            variant.product = product
            variant_form.save()

        return redirect("product_product_detail", pk=product.pk)
    ctx = {
        "product_form": product_form,
        "variant_form": variant_form,
        "product": product,
    }
    return TemplateResponse(request, "product/product_form.html", ctx)


@login_required
@for_htmx(use_block="content")
def product_detail(request, pk):
    products = Product.objects.prefetch_related("variants", "images").all()
    product = get_object_or_404(products, pk=pk)
    variants = product.variants.all()
    ctx = {"object": product, "variants": variants}
    return TemplateResponse(request, "product/product_detail.html", ctx)

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product.objects.prefetch_related("variants"), pk=pk)
    form = ProductForm(request.POST or None, instance=product)

    edit_variant = not product.product_type.has_variants
    if edit_variant:
        variant = product.variants.first()
        variant_form = ProductVariantForm(
            request.POST or None, instance=variant, prefix="variant"
        )
        variant_errors = not variant_form.is_valid()
    else:
        variant_form = None
        variant_errors = False

    if form.is_valid() and not variant_errors:
        product = form.save()
        if edit_variant:
            variant_form.save()
        return redirect("product_product_detail", pk=product.pk)
    ctx = {"product": product, "product_form": form, "variant_form": variant_form}
    return TemplateResponse(request, "product/product_form.html", ctx)


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy("product_product_list")
