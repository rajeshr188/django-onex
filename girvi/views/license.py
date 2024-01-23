from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from utils.htmx_utils import for_htmx

from ..forms import LicenseForm, SeriesForm
from ..models import License, Series


@login_required
@for_htmx(use_block="content")
def license_list(request):
    license = License.objects.all()
    return TemplateResponse(
        request, "girvi/license/license_list.html", context={"object_list": license}
    )


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
