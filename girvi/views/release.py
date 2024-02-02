from datetime import datetime
from typing import List

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView
from django_tables2.config import RequestConfig
from django_tables2.export.export import TableExport
from django_tables2.export.views import ExportMixin
from django_tables2.views import SingleTableMixin

from utils.htmx_utils import for_htmx

from ..filters import ReleaseFilter
from ..forms import BulkReleaseForm, ReleaseForm
from ..models import Loan, Release
from ..tables import ReleaseTable


def increlid():
    try:
        last = Release.objects.latest("id")
        return str(int(last.releaseid) + 1)
    except Release.DoesNotExist:
        return "1"
    except (ValueError, TypeError):
        return "1"


@login_required
@for_htmx(use_block="content")
def release_list(request):
    stats = {}
    filter = ReleaseFilter(
        request.GET,
        queryset=Release.objects.order_by("-id").select_related("created_by"),
    )
    table = ReleaseTable(filter.qs)
    context = {"filter": filter, "table": table}

    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table, exclude_columns=())
        return exporter.response(f"table.{export_format}")
    return TemplateResponse(request, "girvi/release/release_list.html", context)


@login_required
@for_htmx(use_block="content")
def release_create(request, pk=None):
    if request.POST:
        form = ReleaseForm(request.POST or None)
        if form.is_valid():
            form.save()
            # return HttpResponse(status = 200,headers={"HX-Trigger":loanChanged})
            response = redirect(
                "girvi:girvi_loan_detail", pk=form.instance.release_loan.pk
            )
            response["HX-Push-Url"] = reverse(
                "girvi:girvi_loan_detail", kwargs={"pk": form.instance.release_loan.pk}
            )
            return response
    else:
        loan = None
        if pk:
            loan = get_object_or_404(Loan, pk=pk)
            form = ReleaseForm(
                initial={
                    "releaseid": increlid,
                    "release_loan": loan,
                    "created": datetime.now(),
                    "interestpaid": loan.interestdue,
                }
            )
        else:
            form = ReleaseForm(
                initial={
                    "releaseid": increlid,
                    "created": datetime.now(),
                }
            )
    return TemplateResponse(
        request, "girvi/release/release_form.html", context={"form": form}
    )


@login_required
@for_htmx(use_block="content")
def release_detail(request, pk):
    release = get_object_or_404(Release, pk=pk)
    return TemplateResponse(
        request, "girvi/release/release_detail.html", {"object": release}
    )


class ReleaseUpdateView(LoginRequiredMixin, UpdateView):
    model = Release
    form_class = ReleaseForm


class ReleaseDeleteView(LoginRequiredMixin, DeleteView):
    model = Release
    success_url = reverse_lazy("girvi:girvi_release_list")
    template_name = "girvi/release/release_confirm_delete.html"


from django.db import IntegrityError


@for_htmx(use_block="content")
def bulk_release(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = BulkReleaseForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            date = form.cleaned_data["date"]
            loans = form.cleaned_data["loans"]

            if not date:
                date = timezone.now().date()
            new_releases: List[Release] = []
            for loan in loans:
                try:
                    l = Loan.objects.get(loanid=loan.loanid)
                except Loan.DoesNotExist:
                    # raise CommandError(f"Failed to create Release as {loan} does not exist")
                    print(f"Failed to create Release as {loan} does not exist")
                    continue
                try:
                    last_release = Release.objects.latest("id")
                    releaseid = str(int(last_release.releaseid) + 1)
                except Release.DoesNotExist:
                    releaseid = "1"

                new_release = Release(
                    releaseid=releaseid,
                    loan=l,
                    created=date,  # datetime.now(timezone.utc),
                    interestpaid=l.interestdue(date),
                    created_by=request.user,
                )
                new_releases.append(new_release)
            try:
                with transaction.atomic():
                    Release.objects.bulk_create(new_releases)
                    # create journal_entries
            except IntegrityError:
                print("Failed creating Release as already Released")

    # if a GET (or any other method) we'll create a blank form
    else:
        selected_loans = request.GET.getlist("selection", "")
        qs = Loan.unreleased.filter(id__in=selected_loans).values_list("id", flat=True)
        form = BulkReleaseForm(initial={"loans": qs})
    return TemplateResponse(request, "girvi/release/bulk_release.html", {"form": form})


@require_POST
def get_release_details(request):
    # get the loans from request
    loan_ids = request.POST.getlist("loans")  # list of loan ids
    print(loan_ids)
    loans = Loan.objects.filter(id__in=loan_ids).with_details()
    return render(request, "girvi/release/bulk_release_details.html", {"loans": loans})
