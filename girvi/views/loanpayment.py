from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, reverse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from utils.htmx_utils import for_htmx

from ..filters import LoanPaymentFilter
from ..forms import LoanPaymentForm
from ..models import Loan, LoanPayment


@login_required
def loan_payment_list_view(request):
    loan_payments = LoanPayment.objects.all()
    loan_payment_filter = LoanPaymentFilter(request.GET, queryset=loan_payments)
    paginator = Paginator(loan_payment_filter.qs, 50)  # Show 50 loan payments per page

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "loanpayment/loanpayment_list.html",
        {"page_obj": page_obj, "filter": loan_payment_filter},
    )


@login_required
@for_htmx(use_block="content")
def loan_payment_create_view(request, pk=None):
    if request.method == "POST":
        form = LoanPaymentForm(request.POST)
        if form.is_valid():
            loan_payment = form.save(commit=False)
            loan_payment.created_by = request.user
            loan_payment.save()
            return redirect(
                reverse("girvi:girvi_loan_detail", args=[loan_payment.loan.id])
            )
    else:
        initial = {}
        if pk:
            loan = Loan.objects.get(id=pk)
            initial = {"loan": loan, "payment_date": timezone.now()}
        form = LoanPaymentForm(initial=initial)
    return TemplateResponse(
        request, "girvi/loanpayment/loanpayment_form.html", {"form": form}
    )


def loan_payment_update_view(request, pk):
    loan_payment = LoanPayment.objects.get(pk=pk)
    if request.method == "POST":
        form = LoanPaymentForm(request.POST, instance=loan_payment)
        if form.is_valid():
            form.save()
            return redirect("girvi:girvi_loanpayment_list")
    else:
        form = LoanPaymentForm(instance=loan_payment)
    return render(request, "girvi/loanpayment/loanpayment_form.html", {"form": form})


@login_required
@require_http_methods(["DELETE"])
def loan_payment_delete_view(request, pk):
    loan_payment = get_object_or_404(LoanPayment, pk=pk)
    loan_payment.delete()
    return HttpResponse("")
