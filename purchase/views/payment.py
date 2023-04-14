from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django_tables2 import RequestConfig
from num2words import num2words

from utils.htmx_utils import for_htmx

from ..filters import PaymentFilter
from ..forms import PaymentForm
from ..models import Payment
from ..tables import PaymentTable


# use signal to update allotment to associated invoices on create and update
@login_required
@for_htmx(use_block="content")
def payment_list(request):
    filter = PaymentFilter(
        request.GET,
        queryset=Payment.objects.all().select_related("supplier", "created_by"),
    )
    table = PaymentTable(filter.qs)
    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    context = {"filter": filter, "table": table}
    return TemplateResponse(request, "purchase/payment_list.html", context)


def payment_create(request):
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.created_by = request.user
            payment.save()
            return redirect("purchase:purchase_payment_list")
    else:
        form = PaymentForm()
    return render(request, "purchase/payment_form.html", {"form": form})


@login_required
def payment_detail(request, pk):
    payment = get_object_or_404(Payment, id=pk)
    return render(request, "purchase/payment_detail.html", {"object": payment})


@login_required
def payment_update(request, pk):
    payment = get_object_or_404(Payment, id=pk)
    if request.method == "POST":
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.created_by = request.user
            payment.save()
            return redirect("purchase:purchase_payment_list")
    else:
        form = PaymentForm(instance=payment)
    return render(request, "purchase/payment_form.html", {"form": form})


@login_required
def payment_delete(request):
    payment = Payment.objects.get(id=request.POST.get("id"))
    payment.delete()
    return redirect("purchase:purchase_payment_list")


@login_required
def payment_allocate(request, pk):
    payment = get_object_or_404(Payment, id=pk)
    payment.allot()
    return redirect(payment)
