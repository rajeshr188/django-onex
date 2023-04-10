import requests
from django.http import HttpResponse
from ..models import Rate
from django.utils.html import format_html
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

def get_latest_rate(request):
    rate = Rate.objects.latest('timestamp')
    return HttpResponse(f"{rate.metal} {rate.purity} {rate.currency} {rate.buying_rate} {rate.timestamp}")
    

# create list view for rate
@login_required
def rate_list(request):
    rates = Rate.objects.all()
    return render(request, "product/rate_list.html", {"rates": rates})

def rate_delete(request, pk):
    if request.method=='POST':
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
