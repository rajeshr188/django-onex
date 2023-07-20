import datetime
import math

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, F, Max, Prefetch, Q, Sum
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods  # new
from django.views.generic import DeleteView
from django.views.generic.dates import (MonthArchiveView, WeekArchiveView,
                                        YearArchiveView)
from django_tables2.config import RequestConfig
from num2words import num2words
from openpyxl import load_workbook
from render_block import render_block_to_string

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
        queryset=Loan.objects.with_due()
        .with_current_value()
        .with_is_overdue()
        .select_related("customer", "release")
        .prefetch_related("notifications", "loanitems"),
    )
    table = LoanTable(filter.qs)
    stats["total_no_of_loans"] = filter.qs.count()
    context = {"filter": filter, "table": table, "stats": stats}

    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    return TemplateResponse(request, "girvi/loan_list.html", context)


@login_required
def create_loan(request, pk=None):
    form = LoanForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            l = form.save(commit=False)
            l.created_by = request.user
            last_loan = l.save()
            messages.success(request, f"last loan id is {last_loan.lid}")
            if request.htmx:
                print(f"returning 204")
                return HttpResponse(status=204)
            else:
                print("redirecting after succesful creation")
                return redirect("girvi:girvi_loan_create")
        else:
            messages.warning(request, "Please correct the error below.")
            if request.htmx:
                return render(request, "modal-form.html", {"form": form})
            else:
                return render(request, "girvi/loan_form.html", {"form": form})
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


@login_required
def loan_update(request, id=None):
    obj = get_object_or_404(Loan, id=id)
    print(f"{obj} is being updated")
    form = LoanForm(request.POST or None, instance=obj)
    new_item_url = reverse("girvi:girvi_loanitem_create", kwargs={"parent_id": obj.id})
    context = {"form": form, "object": obj, "new_item_url": new_item_url}
    print(f"{obj} updateform is:{form.is_valid()}")
    if form.is_valid():
        print(f"trying to save updated loan")
        form.save()
        context["message"] = "Data saved."
    if request.htmx:
        return render(request, "sales/partials/forms.html", context)
    return render(request, "girvi/create_update.html", context)


class LoanDeleteView(LoginRequiredMixin, DeleteView):
    model = Loan
    success_url = reverse_lazy("girvi:girvi_loan_list")


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
@for_htmx(use_block="loaninfo")
def loan_detail(request, pk):
    loan = get_object_or_404(Loan, pk=pk)
    print(loan.total() < loan.current_value())
    context = {
        "object": loan,
        "sunken": loan.total() < loan.current_value(),
        "items": loan.loanitems.all(),
        "statements": loan.loanstatement_set.all(),
        "loan": loan,
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
        queryset=Loan.objects.with_due().with_current_value().with_is_overdue(),
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


import textwrap

from django.http import HttpResponse
from reportlab.lib.pagesizes import inch, landscape
from reportlab.lib.units import cm, inch
from reportlab.pdfgen import canvas


def generate_original(request, pk=None):
    loan = get_object_or_404(Loan, pk=pk)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="reference_grid.pdf"'

    page_width = 14.6 * cm
    page_height = 21 * cm
    c = canvas.Canvas(response, pagesize=(page_width, page_height))

    # Grid spacing
    grid_spacing = 1 * cm  # Adjust this value based on your preference

    # # Calculate the number of lines
    # num_horizontal_lines = int(page_height / grid_spacing)
    # num_vertical_lines = int(page_width / grid_spacing)

    # # Draw horizontal lines
    # for i in range(num_horizontal_lines):
    #     y = i * grid_spacing
    #     c.line(0, y, page_width, y)

    # # Draw vertical lines
    # for i in range(num_vertical_lines):
    #     x = i * grid_spacing
    #     c.line(x, 0, x, page_height)

    # # Add labels (optional)
    # # You can customize the labels as per your requirements
    # for i in range(num_horizontal_lines):
    #     y = i * grid_spacing
    #     c.drawString(5, y, f"y={y / cm:.2f} cm")

    # for i in range(num_vertical_lines):
    #     x = i * grid_spacing
    #     c.drawString(x, 5, f"x={x / cm:.2f} cm")
    # c.setFont("Courier", 10)
    c.drawString(12 * cm, 18.5 * cm, f"{loan.lid}")
    c.drawString(11.5 * cm, 17.5 * cm, f"{loan.created.strftime('%d-%m-%Y')}")
    c.drawString(2 * cm, 16 * cm, f"{loan.customer}")
    c.drawString(2 * cm, 15 * cm, f"{loan.customer.address.first()}")
    c.drawString(2 * cm, 14 * cm, f"Ph: {loan.customer.contactno.first()}")
    c.drawString(10 * cm, 11.8 * cm, f"{loan.itemweight}")
    c.drawString(10 * cm, 9.8 * cm, f"{loan.itemweight}")
    c.drawString(10 * cm, 8 * cm, f"{loan.itemvalue}")
    c.drawString(6.5*cm,12.2*cm,f"{loan.itemtype}")
    c.drawString(2*cm,6*cm,f"{num2words(loan.loanamount, lang='en_IN')} rupees only")
    if len(loan.itemdesc) > 0:
        wrap_text = textwrap.wrap(loan.itemdesc, width=35)
        c.drawString(2.2 * cm, 11 * cm, wrap_text[0])
        c.drawString(2.2 * cm, 10.5 * cm, wrap_text[1])
    else:
        c.drawString(2.2 * cm, 11 * cm, f"{loan.itemdesc}")

    c.save()

    return response


def generate_duplicate(request, pk=None):
    loan = get_object_or_404(Loan, pk=pk)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="reference_grid.pdf"'

    page_width = 14.6 * cm
    page_height = 21 * cm
    c = canvas.Canvas(response, pagesize=(page_width, page_height))

    # Grid spacing
    grid_spacing = 1 * cm  # Adjust this value based on your preference

    # # Calculate the number of lines
    # num_horizontal_lines = int(page_height / grid_spacing)
    # num_vertical_lines = int(page_width / grid_spacing)

    # # Draw horizontal lines
    # for i in range(num_horizontal_lines):
    #     y = i * grid_spacing
    #     c.line(0, y, page_width, y)

    # # Draw vertical lines
    # for i in range(num_vertical_lines):
    #     x = i * grid_spacing
    #     c.line(x, 0, x, page_height)

    # # Add labels (optional)
    # # You can customize the labels as per your requirements
    # for i in range(num_horizontal_lines):
    #     y = i * grid_spacing
    #     c.drawString(5, y, f"y={y / cm:.2f} cm")

    # for i in range(num_vertical_lines):
    #     x = i * grid_spacing
    #     c.drawString(x, 5, f"x={x / cm:.2f} cm")
    c.drawString(3 * cm, 17.5* cm, f"{loan.lid}")
    c.drawString(11 * cm, 17 * cm, f"{loan.created.strftime('%d-%m-%Y')}")
    c.drawString(5 * cm, 16.8 * cm, f"{loan.customer.name}")
    c.drawString(5 * cm, 15.8 * cm, f"{loan.customer.relatedto}")
    c.drawString(5 * cm, 15 * cm, f"{loan.customer.address.first()}")
    c.drawString(5 * cm, 14 * cm, f"{loan.customer.contactno.first()}")
    c.drawString(5 * cm, 13.5 * cm, f"{loan.loanamount}")
    c.drawString(5 * cm, 13 * cm, f"{num2words(loan.loanamount, lang='en_IN')} rupees only")
    c.drawString(5 * cm, 12.5 * cm, f"{loan.itemtype}")
    # c.drawString(5 * cm, 10 * cm, f"{loan.itemdesc}")
    if len(loan.itemdesc) > 35:
        wrap_text = textwrap.wrap(loan.itemdesc, width=35)
        c.drawString(3 * cm, 10 * cm, wrap_text[0])
        c.drawString(3 * cm, 9.5 * cm, wrap_text[1])
    else:
        c.drawString(3 * cm, 10 * cm, f"{loan.itemdesc}")

    c.drawString(3 * cm, 6.8 * cm, f"{loan.itemweight}")
    c.drawString(12 * cm, 6.8 * cm, f"{loan.itemvalue}")

    c.drawString(4 * cm, 3 * cm, f"{loan.lid }{ loan.created.strftime('%d/%m%y')}")
    c.drawString(4 * cm, 2.5 * cm, f"{loan.loanamount} {loan.itemweight}")
    if len(f"{loan.customer.name} {loan.itemdesc}") > 35:
        wrap_text = textwrap.wrap(f"{loan.customer.name} {loan.itemdesc}", width=35)
        c.drawString(4 * cm, 2 * cm, wrap_text[0])
        c.drawString(4 * cm, 1.5 * cm, wrap_text[1])
    else:
        c.drawString(4 * cm, 2 * cm, f"{loan.itemdesc}")
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


@login_required
def loan_item_update_hx_view(request, parent_id=None, id=None):
    if not request.htmx:
        raise Http404
    try:
        parent_obj = Loan.objects.get(id=parent_id)
    except:
        parent_obj = None
    if parent_obj is None:
        return HttpResponse("Not found.")
    instance = None
    if id is not None:
        try:
            instance = LoanItem.objects.get(loan=parent_obj, id=id)
        except LoanItem.DoesNotExist:
            instance = None
    form = LoanItemForm(request.POST or None, instance=instance)

    url = reverse("girvi:girvi_loanitem_create", kwargs={"parent_id": parent_obj.id})
    if instance:
        url = instance.get_hx_edit_url()
    context = {"url": url, "form": form, "object": instance}
    if form.is_valid():
        new_obj = form.save(commit=False)
        if instance is None:
            new_obj.loan = parent_obj
        new_obj.save()
        context["object"] = new_obj
        if request.htmx:
            return HttpResponse(status=204, headers={"HX-Trigger": "loanChanged"})
        return render(request, "girvi/partials/item-inline.html", context)

    return render(request, "girvi/partials/item-form.html", context)


def get_loan_items(request, loan):
    l = get_object_or_404(Loan, pk=loan)
    items = l.loanitem_set.all()
    return render(request, "", context={"items": items})


def loanitem_delete(request, parent_id, id):
    item = get_object_or_404(LoanItem, id=id, loan_id=parent_id)
    item.delete()
    return HttpResponse(status=204, headers={"HX-Trigger": "loanChanged"})


@login_required
def loanitem_detail(request, pk):
    item = get_object_or_404(LoanItem, pk=pk)
    return render(request, "girvi/partials/item-inline.html", {"object": item})
