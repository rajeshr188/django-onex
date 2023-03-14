from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from girvi.models import Loan
from utils.loan_pdf import get_loan_pdf, get_notice_pdf

from .forms import NoticeGroupForm, NotificationForm
from .models import NoticeGroup, Notification

# Create your views here.


def noticegroup_list(request):
    ng = NoticeGroup.objects.all()
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


def noticegroup_detail(request, pk):
    ng = get_object_or_404(NoticeGroup, pk=pk)
    # loans = Loan.objects.unreleased().filter(
    #     created__gt=ng.date_range.lower, created__lt=ng.date_range.upper
    # )

    return render(
        request,
        "notify/noticegroup_detail.html",
        context={
            "object": ng,
            #  "loans": loans
        },
    )


# views for Notifications


def notification_list(request):
    ng = Notification.objects.all()
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


def noticegroup_print(request, pk):
    ng = get_object_or_404(NoticeGroup, pk=pk)
    selected_loans = []
    for i in ng.notification_set.all():
        for j in i.loans.all():
            selected_loans.append(j.id)
    selected_loans = Loan.objects.unreleased().filter(id__in=selected_loans)
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
