import requests
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import format_html

from ..models import Rate


def get_latest_rate(request):
    grate = Rate.objects.filter(metal=Rate.Metal.GOLD).latest("timestamp")
    srate = Rate.objects.filter(metal=Rate.Metal.SILVER).latest("timestamp")
    return HttpResponse(
        f"{grate.metal} {grate.purity} {grate.currency} {grate.buying_rate} {grate.timestamp}\
           {srate.metal} {srate.purity} {srate.currency} {srate.buying_rate} {srate.timestamp} "
    )


# create list view for rate
@login_required
def rate_list(request):
    rates = Rate.objects.all()
    return render(request, "product/rate_list.html", {"rates": rates})


def rate_delete(request, pk):
    if request.method == "POST":
        rate = get_object_or_404(Rate, pk=pk)
        rate.delete()
    return redirect("rate_list")


@login_required
def rate_create(request):
    if request.method == "POST":
        form = RateForm(request.POST)
        if form.is_valid():
            rate = form.save()
            return redirect("rate_list")
    else:
        form = RateForm()
    return render(request, "product/rate_form.html", {"form": form})
