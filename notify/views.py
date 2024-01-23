from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, reverse
from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods

from girvi.models import Loan
from utils.htmx_utils import for_htmx
from utils.loan_pdf import get_loan_pdf, get_notice_pdf

from .forms import NoticeGroupForm, NotificationForm
from .models import NoticeGroup, Notification

# Create your views here.


def noticegroup_list(request):
    ng = NoticeGroup.objects.all().prefetch_related("notifications")
    return render(request, "notify/noticegroup_list.html", context={"objects": ng})


def noticegroup_create(request):
    form = NoticeGroupForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            object = form.save()
            return render(
                request, "notify/noticegroup_detail.html", context={"object": object}
            )
    return render(request, "notify/noticegroup_form.html", context={"form": form})


@login_required
@for_htmx(use_block="content")
def noticegroup_detail(request, pk):
    ng = get_object_or_404(NoticeGroup, pk=pk)
    # loans = Loan.objects.unreleased().filter(
    #     created__gt=ng.date_range.lower, created__lt=ng.date_range.upper
    # )
    items = (
        ng.notifications.all()
        .prefetch_related(
            "loans",
            "loans__customer",
        )
        .select_related("group", "customer")
    )
    loans = Loan.objects.unreleased().filter(notifications__in=items).count()
    uniquie_customers = (
        Loan.objects.unreleased()
        .filter(notifications__in=items)
        .values("customer")
        .distinct()
        .count()
    )

    return TemplateResponse(
        request,
        "notify/noticegroup_detail.html",
        context={
            "object": ng,
            "items": items,
            "customers": uniquie_customers,
            "loans": loans,
        },
    )


# view to delete a noticegroup
@login_required
@require_http_methods(["DELETE"])
def noticegroup_delete(request, pk):
    ng = get_object_or_404(NoticeGroup, pk=pk)
    ng.delete()
    return HttpResponse(
        status=204, headers={"Hx-Redirect": reverse("notify_noticegroup_list")}
    )


# views for Notifications
@login_required
@require_http_methods(["DELETE"])
def notification_delete(request, pk):
    ng = get_object_or_404(Notification, pk=pk)
    ng.delete()
    return HttpResponse(
        status=204, headers={"Hx-Redirect": reverse("notify_notification_list")}
    )


@login_required
def notification_list(request):
    ng = (
        Notification.objects.all()
        .select_related("group", "customer")
        .prefetch_related("loans", "customer__address", "customer__contactno")
    )
    return render(request, "notify/notification_list.html", context={"objects": ng})


def notification_create(request):
    form = NotificationForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            object = form.save()
            return render(
                request, "notify/notification_detail.html", context={"object": object}
            )
    return render(request, "notify/notification_form.html", context={"form": form})


def notification_detail(request, pk):
    ng = get_object_or_404(Notification, pk=pk)

    return render(request, "notify/notification_detail.html", context={"object": ng})


# this looks heavy on frontend with items > 100: optimise it
def noticegroup_print(request, pk):
    ng = get_object_or_404(NoticeGroup, pk=pk)
    selected_loans = []
    items = ng.notifications.all().prefetch_related("loans")

    print("generated items to print in this noticegroup")
    for i in items:
        for j in i.loans.all():
            selected_loans.append(j.id)
    selected_loans = (
        Loan.objects.unreleased()
        .filter(id__in=selected_loans)
        .order_by("customer")
        .prefetch_related("customer", "loanitems")
    )
    pdf = get_notice_pdf(selection=selected_loans)
    # Create a response object
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="notice.pdf"'
    return response


def notification_print(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    selected_loans = notification.loans.all()
    pdf = get_notice_pdf(selection=selected_loans)
    # Create a response object
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="notice.pdf"'
    return response


def notify_group_msg(request, pk):
    pass


def notify_msg(request, pk):
    pass
