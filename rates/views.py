from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from .models import Rate, RateSource
from .forms import RateForm, RateSourceForm

from django.db.models import Q

# Create your views here.
def get_latest_rate(request):
    latest_rates = Rate.objects.filter(Q(metal=Rate.Metal.GOLD) | Q(metal=Rate.Metal.SILVER)).order_by('metal', '-timestamp').distinct('metal')

    rates = []
    for rate in latest_rates:
        rates.append(f"{rate.metal} {rate.purity} {rate.currency} {rate.buying_rate} {rate.timestamp}")

    return HttpResponse(' '.join(rates))

def rate_list(request):
    rates = Rate.objects.all()
    return render(request, 'rates/rate_list.html', {'rates': rates})

def rate_detail(request, pk):
    rate = get_object_or_404(Rate, pk=pk)
    return render(request, 'rates/rate_detail.html', {'rate': rate})

def rate_create(request):
    if request.method == 'POST':
        form = RateForm(request.POST)
        if form.is_valid():
            rate = form.save()
            return redirect('rate_detail', pk=rate.pk)
    else:
        form = RateForm()
    return render(request, 'rates/rate_form.html', {'form': form})

def rate_update(request, pk):
    rate = get_object_or_404(Rate, pk=pk)
    if request.method == 'POST':
        form = RateForm(request.POST, instance=rate)
        if form.is_valid():
            rate = form.save()
            return redirect('rate_detail', pk=rate.pk)
    else:
        form = RateForm(instance=rate)
    return render(request, 'rates/rate_form.html', {'form': form})

def rate_delete(request, pk):
    rate = get_object_or_404(Rate, pk=pk)
    if request.method == 'POST':
        rate.delete()
        return redirect('rate_list')
    return render(request, 'rates/rate_confirm_delete.html', {'rate': rate})

def ratesource_list(request):
    ratesources = RateSource.objects.all()
    return render(request, 'rates/ratesource_list.html', {'ratesources': ratesources})

def ratesource_detail(request, pk):
    ratesource = get_object_or_404(RateSource, pk=pk)
    return render(request, 'rates/ratesource_detail.html', {'ratesource': ratesource})

def ratesource_create(request):
    if request.method == 'POST':
        form = RateSourceForm(request.POST)
        if form.is_valid():
            ratesource = form.save()
            return redirect('ratesource_detail', pk=ratesource.pk)
    else:
        form = RateSourceForm()
    return render(request, 'rates/ratesource_form.html', {'form': form})

def ratesource_update(request, pk):
    ratesource = get_object_or_404(RateSource, pk=pk)
    if request.method == 'POST':
        form = RateSourceForm(request.POST, instance=ratesource)
        if form.is_valid():
            ratesource = form.save()
            return redirect('ratesource_detail', pk=ratesource.pk)
    else:
        form = RateSourceForm(instance=ratesource)
    return render(request, 'rates/ratesource_form.html', {'form': form})

def ratesource_delete(request, pk):
    ratesource = get_object_or_404(RateSource, pk=pk)
    if request.method == 'POST':
        ratesource.delete()
        return redirect('ratesource_list')
    return render(request, 'rates/ratesource_confirm_delete.html', {'ratesource': ratesource})
