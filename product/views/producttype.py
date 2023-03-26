from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from ..forms import ProductTypeForm
from ..models import ProductType


class ProductTypeListView(LoginRequiredMixin, ListView):
    model = ProductType


class ProductTypeCreateView(LoginRequiredMixin, CreateView):
    model = ProductType
    form_class = ProductTypeForm


class ProductTypeDetailView(LoginRequiredMixin, DetailView):
    model = ProductType


class ProductTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductType
    success_url = reverse_lazy("product_producttype_list")


class ProductTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductType
    form_class = ProductTypeForm
