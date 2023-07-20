from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.shortcuts import render

from girvi.models import Loan, Release
from purchase.models import Invoice as purchaseinvoice
from purchase.models import Payment
from sales.models import Invoice as salesinvoice
from sales.models import Receipt


# Create your views here.
@login_required
def daybook(request):
    q = request.GET.get("q", "")
    if q != "":
        today = datetime.strptime(q, "%d/%m/%Y")
    else:
        today = datetime.today().date()

    yesterday = (today - timedelta(1)).strftime("%d/%m/%Y")
    tomorrow = (today + timedelta(1)).strftime("%d/%m/%Y")

    loan = dict()
    loans = Loan.objects.filter(
        created__year=today.year, created__month=today.month, created__day=today.day
    ).values("loanid", "loanamount")
    loan["loans"] = loans
    loan["total"] = loans.aggregate(t=Sum("loanamount"))

    release = dict()
    releases = Release.objects.filter(
        created__year=today.year, created__month=today.month, created__day=today.day
    ).values("releaseid", "loan__loanamount", "interestpaid")
    release["releases"] = releases
    release["total"] = releases.aggregate(t=Sum("interestpaid"))
    release["releaseamount"] = releases.aggregate(t=Sum("loan__loanamount"))

    sale = salesinvoice.objects.filter(
        created__year=today.year, created__month=today.month, created__day=today.day
    ).with_outstanding_balance()
    purchase = purchaseinvoice.objects.filter(
        created__year=today.year, created__month=today.month, created__day=today.day
    ).with_outstanding_balance()

    receipt = dict()
    rec = Receipt.objects.filter(
        created__year=today.year, created__month=today.month, created__day=today.day
    ).values("type", "total")
    receipt["rec_total"] = rec.annotate(t=Sum("total"))

    payment = dict()
    pay = Payment.objects.filter(
        created__year=today.year, created__month=today.month, created__day=today.day
    ).order_by("type")
    payment["pay_total"] = pay.annotate(t=Sum("total")).order_by("type")

    daybook = dict()
    daybook["yesterday"] = yesterday
    daybook["tomorrow"] = tomorrow
    daybook["date"] = today
    daybook["sale"] = sale
    # daybook['cashsale']=cashsale
    # daybook['creditpur']=creditpur
    daybook["pur"] = purchase
    daybook["receipt"] = receipt
    daybook["payment"] = payment
    daybook["loan"] = loan
    daybook["release"] = release

    context = {"daybook": daybook}
    return render(request, "daybook/daybook.html", context)
