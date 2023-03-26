import datetime
import math
from typing import List

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, F, Max, Prefetch, Q, Sum
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import format_html
from django.views.decorators.http import require_http_methods  # new
from django.views.generic import CreateView, DeleteView, UpdateView
from django.views.generic.dates import (MonthArchiveView, WeekArchiveView,
                                        YearArchiveView)
from django_tables2.config import RequestConfig
from num2words import num2words
from openpyxl import load_workbook
from render_block import render_block_to_string

from contact.models import Customer
from notify.models import NoticeGroup, Notification
from utils.loan_pdf import get_loan_pdf, get_notice_pdf

from ..filters import LoanFilter, LoanStatementFilter
from ..forms import Loan_formset, LoanForm, LoanRenewForm, PhysicalStockForm
from ..models import License, Loan, LoanStatement, Release, Series
from ..tables import LoanTable


class LoanYearArchiveView(LoginRequiredMixin, YearArchiveView):
    queryset = Loan.objects.unreleased()
    date_field = "created"
    make_object_list = True
    allow_future = True


class LoanMonthArchiveView(LoginRequiredMixin, MonthArchiveView):
    queryset = Loan.objects.unreleased()
    date_field = "created"
    make_object_list = True
    allow_future = True


class LoanWeekArchiveView(LoginRequiredMixin, WeekArchiveView):
    queryset = Loan.objects.unreleased()
    date_field = "created"
    week_format = "%W"
    allow_future = True


@login_required
def loan_list(request):
    filter = LoanFilter(request.GET, queryset=Loan.objects.all())
    table = LoanTable(filter.qs)
    context = {"filter": filter, "table": table}

    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    if request.htmx:
        response = render_block_to_string(
            "girvi/loan_list.html", "content", context, request
        )
        return HttpResponse(response)
    else:
        return render(request, "girvi/loan_list.html", context)


# @login_required
# def create_loan(request,pk=None):

#     if pk:
#         customer = get_object_or_404(Customer,pk = pk)

#     if request.method == 'POST':
#         form = LoanForm(request.POST or None)
#         # check whether it's valid:
#         if form.is_valid():
#             l = form.save(commit=False)
#             l.created_by = request.user
#             last_loan = l.save()

#             messages.success(request, f"last loan id is {last_loan.lid}")
#             # return render(request,'girvi/partials/loan_info.html',
#             #     {
#             #         'object':last_loan,
#             #         'previous':last_loan.get_previous(),
#             #         'next':last_loan.get_next(),})
#             reverse_lazy("girvi_loan_create")
#         else:
#             messages.warning(request, 'Please correct the error below.')
#     else:
#         if pk:
#             form = LoanForm(initial={'customer':customer,'created':ld})
#         else:
#             form = LoanForm(initial={'created':ld})

#     if request.META.get('HTTP_HX_REQUEST'):
#         return render(request,'form.html',{'form':form})
#     return render(request,'girvi/loan_form.html',{
#                     'form':form,
#                     })


@login_required
def create_loan(request, pk=None):
    form = LoanForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            l = form.save(commit=False)
            l.created_by = request.user
            last_loan = l.save()

            messages.success(request, f"last loan id is {last_loan.lid}")

            return reverse_lazy("girvi_loan_create")
        else:
            messages.warning(request, "Please correct the error below.")
    else:
        if pk:
            customer = get_object_or_404(Customer, pk=pk)
            form = LoanForm(initial={"customer": customer, "created": ld})
        else:
            form = LoanForm(initial={"created": ld})

    if request.htmx:
        return render(request, "modal-form.html", {"form": form})

    return render(
        request,
        "girvi/loan_form.html",
        {
            "form": form,
        },
    )


# class LoanCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
#     model = Loan
#     form_class = LoanForm
#     success_url = reverse_lazy("girvi_loan_create")

#     def get_template_names(self) -> List[str]:
#         if self.request.htmx:
#             self.template_name = "contact/partials/contact-form-model.html"
#         return super().get_template_names()

#     def get_success_message(self, cleaned_data):
#         return format_html(
#             'created loan {} <a href="/girvi/girvi/loan/detail/{}/"  class="btn btn-outline-info" >{}</a>',
#             self.success_message,
#             self.object.pk,
#             self.object,
#         )

#     def get_initial(self):
#         if self.kwargs:
#             customer = Customer.objects.get(id=self.kwargs["pk"])
#             return {"customer": customer, "created": ld}
#         else:
#             return {"created": ld}

#     def form_valid(self, form):
#         form.instance.created_by = self.request.user
#         return super().form_valid(form)


class LoanUpdateView(LoginRequiredMixin, UpdateView):
    model = Loan
    form_class = LoanForm


class LoanDeleteView(LoginRequiredMixin, DeleteView):
    model = Loan
    success_url = reverse_lazy("girvi_loan_list")


def ld():
    last = Loan.objects.order_by("id").last()
    if not last:
        return datetime.date.today()
    return last.created


@login_required
def next_loanid(request):
    series = request.GET["series"]
    s = get_object_or_404(Series, pk=series)
    lid = s.loan_set.last().lid + 1
    form = LoanForm(initial={"lid": lid})
    context = {
        "field": form["lid"],
    }
    return render(request, "girvi/partials/field.html", context)


@login_required
def post_loan(pk):
    loan = get_object_or_404(Loan, pk=pk)
    if not loan.posted:
        loan.post()
    return redirect(loan)


@login_required
def unpost_loan(pk):
    loan = get_object_or_404(Loan, pk=pk)
    if loan.posted:
        loan.unpost()
    return redirect(loan)


@login_required
def loan_detail(request, pk):
    loan = get_object_or_404(Loan, pk=pk)
    context = {
        "object": loan,
        "loan": loan,
        "next": loan.get_next(),
        "previous": loan.get_previous,
    }

    if request.htmx:
        html = render_block_to_string("girvi/loan_detail.html", "loaninfo", context)
        response = HttpResponse(html)
        return response
    else:
        template = "girvi/loan_detail.html"
        return render(request, template, context)


@login_required
def loan_renew(request, pk):
    loan = get_object_or_404(Loan, pk=pk)

    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = LoanRenewForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            new_loanamount = (
                loan.due() + form.cleaned_data["amount"] + form.cleaned_data["interest"]
            )
            newloan = Loan(
                series=loan.series,
                customer=loan.customer,
                lid=Loan.objects.filter(series=loan.series).latest("lid").lid + 1,
                loanamount=new_loanamount,
                itemweight=loan.itemweight,
                itemdesc=loan.itemdesc,
                interestrate=loan.interestrate,
            )
            Release.objects.create(
                releaseid=Release.objects.latest("id").id + 1,
                loan=loan,
                interestpaid=form.cleaned_data["interest"],
            )
            newloan.save()
            # redirect to a new URL:
            return redirect(newloan)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = LoanRenewForm()
    return render(request, "girvi/loan_renew.html", {"form": form, "loan": loan})


@login_required
def notice(request):
    qyr = request.GET.get("qyr", 0)

    a_yr_ago = timezone.now() - relativedelta(years=int(qyr))

    # get all loans with selected ids
    selected_loans = (
        Loan.objects.unreleased().filter(created__lt=a_yr_ago).order_by("customer")
    )

    # get a list of unique customers for the selected loans
    customers = (
        Customer.objects.filter(loan__in=selected_loans)
        .distinct()
        .prefetch_related("loan_set")
    )

    data = {}

    data["loancount"] = selected_loans.count()
    data["total"] = selected_loans.total()
    data["interest"] = selected_loans.with_interest()
    data["cust"] = customers

    return render(request, "girvi/notice.html", context={"data": data})


@require_http_methods("POST")
@login_required
def deleteLoan(request):
    id_list = request.POST.getlist("selection")
    
    Loan.objects.filter(id__in=id_list).delete()
    filter = LoanFilter(request.GET, queryset=Loan.objects.all())
    table = LoanTable(filter.qs)
    context = {"filter": filter, "table": table}
    RequestConfig(request, paginate={"per_page": 10}).configure(table)

    response = render_block_to_string(
        "girvi/loan_list.html", "content", context, request
    )
    return HttpResponse(response)


@login_required
def notify_print(request):
    # check if user wanted all rows to be selected
    all = request.POST.get("selectall")
    selected_loans = None

    if all == "selected":
        # get query parameters if all row selected and retrive queryset
        filter = LoanFilter(request.GET, queryset=Loan.objects.unreleased().all())

        selected_loans = filter.qs.order_by("customer")
    else:
        # get the selected loan ids from the request
        selection = request.POST.getlist("selection")

        selected_loans = Loan.unreleased.filter(id__in=selection).order_by("customer")

    ng = NoticeGroup.objects.create(name=datetime.datetime.now())
    customers = Customer.objects.filter(loan__in=selected_loans).distinct()
    for customer in customers:
        ni = Notification.objects.create(
            group=ng,
            customer=customer,
        )
        ni.loans.set(selected_loans.filter(customer=customer))
        ni.save()
    return HttpResponse(status=204)


@login_required
def multirelease(request, id=None):
    if request.method == "POST":  # <- Checking for method type
        id_list = request.POST.getlist("selection")
        action = request.POST.get("action")

        if action == "delete":
            # delete all selected rows
            Loan.objects.filter(id__in=id_list).delete()

        elif action == "release":
            print("in releaseaction")
            for loan_id in id_list:
                last = Release.objects.all().order_by("id").last()
                if not last:
                    return "1"
                Release.objects.create(
                    releaseid=int(last.id) + 1,
                    created=timezone.now(),
                    loan_id=loan_id,
                    interestpaid=0,
                )

    return HttpResponseRedirect(reverse("girvi_loan_list"))


@user_passes_test(lambda user: user.is_superuser)
@login_required
def home(request):
    data = dict()
    today = datetime.date.today()

    loan = dict()
    loans = Loan.objects
    released = Loan.released
    unreleased = Loan.unreleased

    customer = dict()
    c = Customer.objects

    customer["maxloans"] = (
        c.filter(loan__release__isnull=True)
        .annotate(
            num_loans=Count("loan"),
            sum_loans=Sum("loan__loanamount"),
            tint=Sum("loan__interest"),
        )
        .values("name", "num_loans", "sum_loans", "tint")
        .order_by("-num_loans", "sum_loans", "tint")[:10]
    )
    license = dict()
    l = License.objects.all()
    license["count"] = l.count()
    # license['licenses']=','.join(lic.name for lic in l.all())
    series = Series.objects.all()
    license["totalloans"] = series.annotate(
        t=Coalesce(Sum("loan__loanamount", filter=Q(loan__release__isnull=True)), 0)
    )
    license["totalunreleasedloans"] = series.annotate(
        t=Coalesce(Sum("loan__loanamount", filter=Q(loan__release__isnull=False)), 0)
    )
    license["licchart"] = list(license["totalloans"])
    license["licunrchart"] = list(license["totalunreleasedloans"])

    loan["total_loans"] = loans.count()
    loan["released_loans"] = released.count()
    loan["unreleased_loans"] = loan["total_loans"] - loan["released_loans"]

    l = unreleased
    loan["count"] = l.count()

    loan["amount"] = l.aggregate(t=Coalesce(Sum("loanamount"), 0))
    loan["amount_words"] = num2words(loan["amount"]["t"], lang="en_IN")
    loan["gold_amount"] = l.filter(itemtype="Gold").aggregate(t=Sum("loanamount"))
    loan["gold_weight"] = l.filter(itemtype="Gold").aggregate(t=Sum("itemweight"))
    loan["gavg"] = math.ceil(loan["gold_amount"]["t"] / loan["gold_weight"]["t"])
    loan["silver_amount"] = l.filter(itemtype="Silver").aggregate(t=Sum("loanamount"))
    loan["silver_weight"] = l.filter(itemtype="Silver").aggregate(t=Sum("itemweight"))
    loan["savg"] = math.ceil(loan["silver_amount"]["t"] / loan["silver_weight"]["t"])
    loan["interestdue"] = l.aggregate(t=Sum("interest"))

    sumbyitem = l.aggregate(
        gold=Sum("loanamount", filter=Q(itemtype="Gold")),
        silver=Sum("loanamount", filter=Q(itemtype="Silver")),
        bronze=Sum("loanamount", filter=Q(itemtype="Bronze")),
    )
    fixed = []
    fixed.append(sumbyitem["gold"])
    fixed.append(sumbyitem["silver"])
    fixed.append(sumbyitem["bronze"])
    loan["sumbyitem"] = fixed
    datetimel = (
        loans.annotate(year=ExtractYear("created"))
        .values("year")
        .annotate(l=Sum("loanamount"))
        .order_by("year")
        .values_list("year", "l", named=True)
    )

    datetime2 = (
        unreleased.annotate(year=ExtractYear("created"))
        .values("year")
        .annotate(l=Sum("loanamount"))
        .order_by("year")
        .values_list("year", "l", named=True)
    )

    thismonth = (
        loans.filter(Q(created__year=today.year) & Q(created__month=today.month))
        .annotate(date_only=F("created__day"))
        .values("date_only")
        .annotate(t=Sum("loanamount"))
        .order_by("date_only")
        .values_list("date_only", "t", named=True)
    )

    lastmonth = (
        loans.filter(Q(created__year=today.year) & Q(created__month=today.month - 1))
        .annotate(date_only=F("created__day"))
        .values("date_only")
        .annotate(t=Sum("loanamount"))
        .order_by("date_only")
        .values_list("date_only", "t", named=True)
    )

    thisyear = (
        loans.filter(created__year=today.year)
        .annotate(month=ExtractMonth("created"))
        .values("month")
        .order_by("month")
        .annotate(t=Sum("loanamount"))
        .values_list("month", "t", named="True")
    )

    lastyear = (
        loans.filter(created__year=today.year - 1)
        .annotate(month=ExtractMonth("created"))
        .values("month")
        .order_by("month")
        .annotate(t=Sum("loanamount"))
        .values_list("month", "t", named="True")
    )

    loan["status"] = [loans.count(), released.count()]

    loan["datechart"] = datetimel
    loan["datechart1"] = datetime2
    loan["thismonth"] = thismonth
    loan["lastmonth"] = lastmonth
    loan["thisyear"] = thisyear
    loan["lastyear"] = lastyear
    release = dict()
    r = Release.objects
    release["count"] = r.count()

    data["customer"] = customer
    data["license"] = license
    data["loan"] = loan
    data["interestdue"] = Loan.objects.unreleased().with_interest()
    data["release"] = release
    if request.META.get("HTTP_HX_REQUEST"):
        return render(
            request,
            "girvi/partials/home.html",
            context={"data": data},
        )
    return render(
        request,
        "girvi/home.html",
        context={"data": data},
    )


@login_required
def check_girvi(request):
    data = {}
    if request.method == "POST" and request.FILES["myfile"]:
        myfile = request.FILES["myfile"]

        wb = load_workbook(myfile, read_only=True)
        sheet = wb.active

        django_set = set()
        physical_set = set()
        for l in Loan.unreleased.filter(itemtype="Gold").values("loanid"):
            django_set.add(l["loanid"])
        for r in sheet.iter_rows(min_row=0):
            physical_set.add(r[0].value)

        data["records"] = len(django_set)
        data["items"] = len(physical_set)

        data["missing_records"] = list(physical_set - django_set)
        data["missing_items"] = list(django_set - physical_set)

        return render(request, "girvi/girvi_upload.html", context={"data": data})

    return render(request, "girvi/girvi_upload.html")


@login_required
def physical_stock(request):
    if request.method == "POST":
        form = PhysicalStockForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            date = form.cleaned_data["date"]
            loans = form.cleaned_data["loans"]
            if not date:
                date = timezone.now().date()

            for i in loans:
                print(i)
                ls = LoanStatement.objects.create(created=date, loan=i)
                print(ls)
    else:
        form = PhysicalStockForm()
    return render(request, "girvi/physicalstock.html", {"form": form})


@login_required
def physical_list(request):
    physically_available = LoanStatement.objects.filter(
        pk__in=LoanStatement.objects.order_by()
        .values("loan_id")
        .annotate(max_id=Max("id"))
        .values("max_id")
    )
    filter = LoanStatementFilter(request.GET, queryset=physically_available)

    return render(request, "girvi/physicallist.html", {"filter": filter})


@login_required
def print_loan(request, pk=None):
    loan = get_object_or_404(Loan, pk=pk)
    pdf = get_loan_pdf(loan=loan)
    # Create a response object
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="pledge.pdf"'
    return response