from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from ..forms import LicenseForm, SeriesForm
from ..models import License, Series


class LicenseListView(LoginRequiredMixin, ListView):
    model = License


class LicenseCreateView(LoginRequiredMixin, CreateView):
    model = License
    form_class = LicenseForm


class LicenseDetailView(LoginRequiredMixin, DetailView):
    model = License


class LicenseUpdateView(LoginRequiredMixin, UpdateView):
    model = License
    form_class = LicenseForm


class LicenseDeleteView(LoginRequiredMixin, DeleteView):
    model = License
    success_url = reverse_lazy("girvi:girvi_license_list")


def activate_series(request, pk):
    s = get_object_or_404(Series, pk=pk)
    s.activate()
    return redirect("girvi:girvi_loan_list")


class SeriesListView(LoginRequiredMixin, ListView):
    model = Series


class SeriesCreateView(LoginRequiredMixin, CreateView):
    model = Series
    form_class = SeriesForm


class SeriesDetailView(LoginRequiredMixin, DetailView):
    model = Series


class SeriesUpdateView(LoginRequiredMixin, UpdateView):
    model = Series
    form_class = SeriesForm


class LicenseSeriesDeleteView(LoginRequiredMixin, DeleteView):
    model = License
    success_url = reverse_lazy("girvi:girvi_license_list")
