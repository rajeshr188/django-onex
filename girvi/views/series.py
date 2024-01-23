from django.shortcuts import get_object_or_404, redirect, render

from ..forms import SeriesForm
from ..models import Series


# create views to crud series
def series_list(request):
    series = Series.objects.all()
    return render(request, "girvi/series/series_list.html", {"series": series})


def series_detail(request, pk):
    series = get_object_or_404(Series, pk=pk)
    return render(request, "girvi/series/series_detail.html", {"series": series})


def series_new(request):
    if request.method == "POST":
        form = SeriesForm(request.POST)
        if form.is_valid():
            series = form.save(commit=False)
            series.save()
            return redirect("series_detail", pk=series.pk)
    else:
        form = SeriesForm()
    return render(request, "girvi/series/series_edit.html", {"form": form})


def series_edit(request, pk):
    series = get_object_or_404(Series, pk=pk)
    if request.method == "POST":
        form = SeriesForm(request.POST, instance=series)
        if form.is_valid():
            series = form.save(commit=False)
            series.save()
            return redirect("series_detail", pk=series.pk)
    else:
        form = SeriesForm(instance=series)
    return render(request, "girvi/series/series_edit.html", {"form": form})


def series_delete(request, pk):
    series = get_object_or_404(Series, pk=pk)
    series.delete()
    return redirect("series_list")
