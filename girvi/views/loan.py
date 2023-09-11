import base64
import datetime
import math
import textwrap

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.db.models import Count, F, Max, Prefetch, Q, Sum
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods  # new
from django.views.generic import DeleteView
from django.views.generic.dates import (
    MonthArchiveView,
    WeekArchiveView,
    YearArchiveView,
)
from django_tables2.config import RequestConfig
from django_tables2.export.export import TableExport
from num2words import num2words
from openpyxl import load_workbook
from render_block import render_block_to_string
from reportlab.lib.pagesizes import inch, landscape
from reportlab.lib.units import cm, inch
from reportlab.pdfgen import canvas

from contact.models import Customer
from notify.models import NoticeGroup, Notification
from utils.htmx_utils import for_htmx
from utils.loan_pdf import get_loan_pdf, get_notice_pdf

from ..filters import LoanFilter, LoanStatementFilter
from ..forms import LoanForm, LoanItemForm, LoanRenewForm, PhysicalStockForm
from ..models import License, Loan, LoanItem, LoanStatement, Release, Series
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
@for_htmx(use_block="content")
def loan_list(request):
    stats = {}
    filter = LoanFilter(
        request.GET,
        queryset=Loan.objects.order_by("-id")
        .with_details()
        .prefetch_related("notifications", "loanitems"),
    )
    table = LoanTable(filter.qs)
    context = {"filter": filter, "table": table}

    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table, exclude_columns=("selection"))
        return exporter.response(f"table.{export_format}")
    return TemplateResponse(request, "girvi/loan_list.html", context)


@login_required
# @for_htmx(use_block="content")
def create_loan(request, pk=None):
    form = LoanForm(request.POST or None, request.FILES)

    if request.method == "POST":
        if form.is_valid():
            l = form.save(commit=False)
            l.created_by = request.user

            image_data = request.POST.get("image_data")

            if image_data:
                image_file = ContentFile(
                    base64.b64decode(image_data.split(",")[1]),
                    name=f"{l.loanid}__{l.customer.name}_{l.id}.jpg",
                )

                l.pic = image_file
            l.save()
            messages.success(request, f"last loan id is {l}")
            # return HttpResponse(status=200,headers ={"Hx-Redirect":l.get_absolute_url()})
            response = render_block_to_string(
                "girvi/loan_detail.html",
                "content",
                {
                    "loan": l,
                    "object": l,
                },
                request,
            )
            return HttpResponse(
                response,
                headers={
                    "Hx-Push-Url": reverse(
                        "girvi:girvi_loan_detail", kwargs={"pk": l.id}
                    )
                },
            )

        else:
            messages.warning(request, "Please correct the error below.")
            response = render_block_to_string(
                "girvi/loan_form.html", "content", {"form": form}, request
            )
            return HttpResponse(response)
            # return TemplateResponse(request, "girvi/loan_form.html", {"form": form})
    else:
        series = Loan.objects.latest().series
        lid = series.loan_set.last().lid + 1
        initial = {
            "created": datetime.datetime.now(),
            "series": series,
            "lid": lid,
        }
        if pk:
            # creating loan for the given customer
            initial["customer"] = get_object_or_404(Customer, pk=pk)

        form = LoanForm(initial=initial)
        if request.htmx:
            response = render_block_to_string(
                "girvi/loan_form.html", "content", {"form": form}, request
            )
            return HttpResponse(response)
    return TemplateResponse(
        request,
        "girvi/loan_form.html",
        {
            "form": form,
        },
    )


@login_required
def loan_update(request, id=None):
    obj = get_object_or_404(Loan, id=id)

    form = LoanForm(request.POST or None, instance=obj)
    new_item_url = reverse("girvi:girvi_loanitem_create", kwargs={"parent_id": obj.id})
    context = {"form": form, "object": obj, "new_item_url": new_item_url}

    if form.is_valid():
        form.save()
        context["message"] = "Data saved."
    if request.htmx:
        return render(request, "girvi/partials/forms.html", context)
    return render(request, "girvi/create_update.html", context)


class LoanDeleteView(LoginRequiredMixin, DeleteView):
    model = Loan
    success_url = reverse_lazy("girvi:girvi_loan_list")


def ld():
    last = Loan.objects.order_by("id").last()
    if not last:
        return datetime.date.today()
    return last.created


def get_interestrate(request):
    metal = request.GET["itemtype"]
    interest = 0
    if metal == "Gold":
        interest = 2
    elif metal == "Silver":
        interest = 4
    else:
        interest = 8
    form = LoanItemForm(initial={"interestrate": interest})
    context = {
        "field": form["interestrate"],
    }
    return render(request, "girvi/partials/field.html", context)


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
@for_htmx(use_block_from_params=True)
def loan_detail(request, pk):
    loan = get_object_or_404(Loan, pk=pk)

    context = {
        "object": loan,
        "sunken": loan.total() < loan.current_value(),
        "items": loan.loanitems.all(),
        "statements": loan.loanstatement_set.all(),
        "loan": loan,
        "weight": loan.get_total_weight(),
        "next": loan.get_next(),
        "journals": loan.journals.all(),
        "previous": loan.get_previous,
        "new_item_url": reverse(
            "girvi:girvi_loanitem_create", kwargs={"parent_id": loan.id}
        ),
    }

    return TemplateResponse(request, "girvi/loan_detail.html", context)


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
    data["total"] = selected_loans.with_total_loanamount()
    data["interest"] = selected_loans.with_total_interest()
    data["cust"] = customers

    return render(request, "girvi/notice.html", context={"data": data})


@require_http_methods("POST")
@login_required
def deleteLoan(request):
    id_list = request.POST.getlist("selection")
    loans = Loan.objects.filter(id__in=id_list)
    for i in loans:
        i.delete()
    filter = LoanFilter(
        request.GET,
        queryset=Loan.objects.with_due()
        .with_current_value()
        .with_is_overdue()
        .with_weight(),
    )
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
        print("all selected")
        # get query parameters if all row selected and retrive queryset
        print(request.GET)
        filter = LoanFilter(
            request.GET,
            queryset=Loan.objects.with_due()
            .with_current_value()
            .with_is_overdue()
            .select_related("customer", "release")
            .prefetch_related("notifications", "loanitems"),
        )

        selected_loans = filter.qs.order_by("customer")
        print(f"selected loans: {selected_loans.count()}")
    else:
        print("partially selected")
        # get the selected loan ids from the request
        selection = request.POST.getlist("selection")

        selected_loans = (
            Loan.objects.unreleased().filter(id__in=selection).order_by("customer")
        )

    # ng = NoticeGroup.objects.create(name=datetime.datetime.now())
    # # optimise this
    # customers = Customer.objects.filter(loan__in=selected_loans).distinct()
    # for customer in customers:
    #     try:
    #         ni = Notification.objects.create(
    #             group=ng,
    #             customer=customer,
    #         )
    #         ni.loans.set(selected_loans.filter(customer=customer))
    #         ni.save()
    #     except IntegrityError:
    #         print("Error adding notification for customer {}".format(customer.id))
    ng = NoticeGroup.objects.create(name=datetime.datetime.now())

    # Get a queryset of customers with selected loans
    customers = Customer.objects.filter(loan__in=selected_loans).distinct()

    # Create a list of Notification objects to create
    notifications_to_create = []
    for customer in customers:
        notifications_to_create.append(
            Notification(
                group=ng,
                customer=customer,
            )
        )

    # Use bulk_create to create the notifications
    try:
        notifications = Notification.objects.bulk_create(notifications_to_create)
    except IntegrityError:
        print("Error adding notifications.")

    # Add loans to the notifications
    for notification in notifications:
        loans = selected_loans.filter(customer=notification.customer)
        notification.loans.set(loans)
        notification.save()

    # return HttpResponse(status=204)
    return redirect(ng)


@login_required
def print_loan(request, pk=None):
    loan = get_object_or_404(Loan, pk=pk)
    pdf = get_loan_pdf(loan=loan)
    # Create a response object
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="pledge.pdf"'
    return response


def generate_original(request, pk=None):
    loan = get_object_or_404(Loan, pk=pk)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename='{loan.lid}.pdf'"

    page_width = 14.6 * cm
    page_height = 21 * cm
    c = canvas.Canvas(response, pagesize=(page_width, page_height))

    # Grid spacing
    grid_spacing = 1 * cm  # Adjust this value based on your preference
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(12 * cm, 18.2 * cm, f"{loan.lid}")
    c.drawString(11.5 * cm, 17.2 * cm, f"{loan.created.strftime('%d-%m-%Y')}")

    # Wrap the text if its length is greater than 35 characters
    customer = f"{loan.customer.name} {loan.customer.get_relatedas_display()} {loan.customer.relatedto}"
    lines = textwrap.wrap(customer, width=35)
    # Draw the wrapped text on the canvas
    y = 15.5 * cm
    for line in lines:
        c.drawString(2 * cm, y, line)
        y -= 0.5 * cm
    c.setFont("Helvetica", 12)
    address = f"{loan.customer.address.first()}"
    lines = textwrap.wrap(address, width=35)
    # Draw the wrapped text on the canvas
    y = 15 * cm
    for line in lines:
        c.drawString(2 * cm, y, line)
        y -= 0.5 * cm
    c.setFont("Helvetica", 12)
    c.drawString(2 * cm, 14 * cm, f"Ph: {loan.customer.contactno.first()}")
    c.drawString(10 * cm, 11.8 * cm, f"{loan.itemweight}")
    c.drawString(10 * cm, 9.8 * cm, f"{loan.itemweight}")
    c.drawString(10 * cm, 8 * cm, f"{loan.loanamount +500}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(7 * cm, 12.5 * cm, f"{loan.itemtype}")
    c.drawString(8 * cm, 6.5 * cm, f"{loan.loanamount}")
    # Wrap the text if its length is greater than 35 characters
    lines = textwrap.wrap(loan.itemdesc, width=30)
    # Draw the wrapped text on the canvas
    y = 11 * cm
    for line in lines:
        c.drawString(2.5 * cm, y, line)
        y -= 0.5 * cm

    c.setFont("Helvetica", 12)
    c.drawString(
        2 * cm, 6 * cm, f"{num2words(loan.loanamount, lang='en_IN')} rupees only"
    )

    c.save()
    return response


def generate_duplicate(request, pk=None):
    loan = get_object_or_404(Loan, pk=pk)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename='{loan.lid}.pdf'"

    page_width = 14.6 * cm
    page_height = 21 * cm
    c = canvas.Canvas(response, pagesize=(page_width, page_height))
    c.setFont("Helvetica", 12)
    # Grid spacing
    grid_spacing = 1 * cm  # Adjust this value based on your preference

    c.drawString(3 * cm, 17 * cm, f"{loan.lid}")
    c.drawString(11 * cm, 17 * cm, f"{loan.created.strftime('%d-%m-%Y')}")
    c.drawString(5 * cm, 16.5 * cm, f"{loan.customer.name}")
    c.drawString(
        5 * cm,
        16 * cm,
        f"{loan.customer.get_relatedas_display()} {loan.customer.relatedto}",
    )
    address = textwrap.wrap(f"{loan.customer.address.first()}")
    # Draw the wrapped text on the canvas
    y = 15 * cm
    for line in address:
        c.drawString(5 * cm, y, line)
        y -= 0.5 * cm

    c.drawString(5 * cm, 14 * cm, f"{loan.customer.contactno.first()}")
    c.drawString(5 * cm, 13.5 * cm, f"{loan.loanamount}")

    lines = textwrap.wrap(
        f"{num2words(loan.loanamount, lang='en_IN')} rupees only", width=45
    )
    # Draw the wrapped text on the canvas
    y = 13 * cm
    for line in lines:
        c.drawString(5 * cm, y, line)
        y -= 0.5 * cm

    c.drawString(5 * cm, 12.1 * cm, f"{loan.itemtype}")

    # Wrap the text if its length is greater than 35 characters
    lines = textwrap.wrap(loan.itemdesc, width=35)
    # Draw the wrapped text on the canvas
    y = 10 * cm
    for line in lines:
        c.drawString(3 * cm, y, line)
        y -= 0.5 * cm

    c.drawString(5 * cm, 7 * cm, f"{loan.itemweight}")
    c.drawString(8 * cm, 7 * cm, f"{loan.itemweight}")
    c.drawString(12 * cm, 7 * cm, f"{loan.itemvalue}")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * cm, 3.5 * cm, f"{loan.lid}")
    c.drawString(1 * cm, 3 * cm, f"{loan.created.strftime('%d/%m/%y')}")
    c.drawString(1 * cm, 2.5 * cm, f"{loan.loanamount}   {loan.itemweight} gm")
    c.drawString(1 * cm, 2 * cm, f"{loan.customer.name}")
    # Wrap the text if its length is greater than 35 characters
    lines = textwrap.wrap(f"{loan.itemdesc}", width=35)
    # Draw the wrapped text on the canvas
    y = 1.5 * cm
    for line in lines:
        c.drawString(1 * cm, y, line)
        y -= 0.5 * cm

    c.save()
    return response


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

    return HttpResponseRedirect(reverse("girvi:girvi_loan_list"))


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


# @login_required
# def loan_item_update_hx_view(request, parent_id=None, id=None):
#     if not request.htmx:
#         raise Http404

#     try:
#         parent_obj = Loan.objects.get(id=parent_id)
#     except Loan.DoesNotExist:
#         return HttpResponse("Not found.")

#     instance = None
#     if id is not None:
#         try:
#             instance = LoanItem.objects.get(loan=parent_obj, id=id)
#         except LoanItem.DoesNotExist:
#             instance = None

#     form = LoanItemForm(request.POST or None,instance=instance)

#     url = reverse("girvi:girvi_loanitem_create", kwargs={"parent_id": parent_obj.id})
#     if instance:
#         url = instance.get_hx_edit_url()
#     context = {"url": url, "form": form, "object": instance}
#     if form.is_valid():
#         new_obj = form.save(commit=False)
#         if instance is None:
#             new_obj.loan = parent_obj
#         new_obj.save()
#         context["object"] = new_obj
#         if request.htmx:
#             return HttpResponse(status=204, headers={"HX-Trigger": "loanChanged"})
#         return render(request, "girvi/partials/item-inline.html", context)

#     return render(request, "girvi/partials/item-form.html", context)


@login_required
def loan_item_update_hx_view(request, parent_id=None, id=None):
    if not request.htmx:
        raise Http404("This view is meant for Htmx requests only.")

    try:
        parent_obj = Loan.objects.get(id=parent_id)
    except Loan.DoesNotExist:
        return HttpResponse("Not found.", status=404)

    instance = None
    if id is not None:
        try:
            instance = LoanItem.objects.get(loan=parent_obj, id=id)
        except LoanItem.DoesNotExist:
            instance = None

    if request.method == "POST":
        form = LoanItemForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            new_obj = form.save(commit=False)
            if instance is None:
                new_obj.loan = parent_obj
            image_data = request.POST.get("image_data")

            if image_data:
                image_file = ContentFile(
                    base64.b64decode(image_data.split(",")[1]),
                    name=f"{new_obj.loan.loanid}_{new_obj.id}.jpg",
                )

                new_obj.pic = image_file
            new_obj.save()
            context = {"object": new_obj}

            if request.htmx:
                return HttpResponse(status=204, headers={"HX-Trigger": "loanChanged"})
            return render(request, "girvi/partials/item-inline.html", context)
        else:
            context = {"url": url, "form": form, "object": instance}
            return render(request, "girvi/partials/item-form.html", context)

    else:
        form = LoanItemForm(instance=instance)

    url = reverse("girvi:girvi_loanitem_create", kwargs={"parent_id": parent_obj.id})
    if instance:
        url = instance.get_hx_edit_url()

    context = {"url": url, "form": form, "object": instance}
    return render(request, "girvi/partials/item-form.html", context)


@login_required
def get_loan_items(request, loan):
    l = get_object_or_404(Loan, pk=loan)
    items = l.loanitem_set.all()
    return render(request, "", context={"items": items})


@login_required
def loanitem_delete(request, parent_id, id):
    item = get_object_or_404(LoanItem, id=id, loan_id=parent_id)
    loan = item.loan
    item.delete()
    loan.save()
    return HttpResponse(status=204, headers={"HX-Trigger": "loanChanged"})


@login_required
def loanitem_detail(request, pk):
    item = get_object_or_404(LoanItem, pk=pk)
    return render(request, "girvi/partials/item-inline.html", {"object": item})
