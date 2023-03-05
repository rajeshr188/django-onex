from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from ..forms import (
    AttributeForm,
    AttributeValueForm,
    ProductImageForm,
    VariantImageForm,
)
from ..models import Attribute, AttributeValue, ProductImage, VariantImage

# from ..filters import ProductFilter,ProductVariantFilter,StockFilterfrom django.shortcuts import get_object_or_404,redirect, render


# from blabel import Labelwriter


class AttributeListView(LoginRequiredMixin, ListView):
    model = Attribute


class AttributeCreateView(LoginRequiredMixin, CreateView):
    model = Attribute
    form_class = AttributeForm


class AttributeDetailView(LoginRequiredMixin, DetailView):
    model = Attribute


class AttributeUpdateView(LoginRequiredMixin, UpdateView):
    model = Attribute
    form_class = AttributeForm


class AttributeValueListView(LoginRequiredMixin, ListView):
    model = AttributeValue


class AttributeValueCreateView(LoginRequiredMixin, CreateView):
    model = AttributeValue
    form_class = AttributeValueForm


class AttributeValueDetailView(LoginRequiredMixin, DetailView):
    model = AttributeValue


class AttributeValueUpdateView(LoginRequiredMixin, UpdateView):
    model = AttributeValue
    form_class = AttributeValueForm


class ProductImageListView(LoginRequiredMixin, ListView):
    model = ProductImage


class ProductImageCreateView(LoginRequiredMixin, CreateView):
    model = ProductImage
    form_class = ProductImageForm


class ProductImageDetailView(LoginRequiredMixin, DetailView):
    model = ProductImage


class ProductImageUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductImage
    form_class = ProductImageForm


class VariantImageListView(LoginRequiredMixin, ListView):
    model = VariantImage


class VariantImageCreateView(LoginRequiredMixin, CreateView):
    model = VariantImage
    form_class = VariantImageForm


class VariantImageDetailView(LoginRequiredMixin, DetailView):
    model = VariantImage


class VariantImageUpdateView(LoginRequiredMixin, UpdateView):
    model = VariantImage
    form_class = VariantImageForm
