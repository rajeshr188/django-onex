from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, UpdateView
from django_filters.views import FilterView

from ..filters import ProductVariantFilter
from ..forms import ProductVariantForm
from ..models import Product, ProductVariant


class ProductVariantListView(LoginRequiredMixin, FilterView):
    model = ProductVariant
    filterset_class = ProductVariantFilter
    template_name = "product/productvariant_list.html"


@login_required
def variant_create(request, pk):
    track_inventory = True
    product = get_object_or_404(Product.objects.all(), pk=pk)
    variant = ProductVariant(product=product, track_inventory=track_inventory)
    form = ProductVariantForm(request.POST or None, instance=variant)
    if form.is_valid():
        form.save()
        return redirect("product_productvariant_detail", pk=variant.pk)
    ctx = {"form": form, "product": product, "variant": variant}
    return TemplateResponse(request, "product/productvariant_form.html", ctx)


class ProductVariantDetailView(LoginRequiredMixin, DetailView):
    model = ProductVariant


class ProductVariantUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductVariant
    form_class = ProductVariantForm


class ProductVariantDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductVariant
    success_url = reverse_lazy("product_productvariant_list")
