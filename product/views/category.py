from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from ..forms import CategoryForm
from ..models import Category


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm


class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = Category


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
