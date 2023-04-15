from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.http.response import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import DeleteView

from dea.models import Journal
from invoice.models import PaymentTerm
from sales.models import Invoice as sinv
from sales.models import InvoiceItem as sinvitem
from utils.htmx_utils import for_htmx

from .filters import ApprovalFilter, ApprovalLineFilter
from .forms import ApprovalForm, ApprovalLineForm, ReturnForm, ReturnItemForm
from .models import Approval, ApprovalLine, Return, ReturnItem


@login_required
def convert_sales(request, pk):
    # create sales invoice and invoice items from approval
    approval = get_object_or_404(Approval, pk=pk)
    term = PaymentTerm.objects.first()

    sale = sinv.objects.create(
        created=datetime.now(), customer=approval.contact, approval=approval, term=term
    )
    for item in approval.items.all():
        i = sinvitem.objects.create(
            invoice=sale,
            product=item.product,
            weight=item.weight,
            quantity=item.quantity,
            touch=item.touch,
            total=(item.weight * item.touch) / 100,
        )
        i.save()

    sale.gross_wt = sale.get_gross_wt()
    sale.net_wt = sale.get_net_wt()
    sale.balance = sale.get_balance()
    sale.save()
    approval.is_billed = True
    approval.save()
    return redirect(sale)


@login_required
# @for_htmx(use_block="table")
def approval_list(request):
    approvals = Approval.objects.all()
    filter = ApprovalFilter(request.GET, queryset=approvals)
    return render(request, "approval/approval_list.html", {"filter": filter})


@login_required
def approval_create(request):
    if request.method == "POST":
        form = ApprovalForm(request.POST)
        if form.is_valid():
            approval = form.save(commit=False)
            approval.save()
            return redirect(approval)
    else:
        form = ApprovalForm()
    return render(request, "approval/approval_form.html", {"form": form})


@login_required
@for_htmx(use_block="content")
def approval_detail(request, pk):
    approval = get_object_or_404(Approval, pk=pk)

    return TemplateResponse(
        request,
        "approval/approval_detail.html",
        {
            "object": approval,
        },
    )


@login_required
def approval_update(request, pk):
    approval = get_object_or_404(Approval, pk=pk)
    if request.method == "POST":
        form = ApprovalForm(request.POST, instance=approval)
        if form.is_valid():
            approval = form.save(commit=False)
            approval.save()
            return redirect(approval)
    else:
        form = ApprovalForm(instance=approval)
    return render(
        request,
        "approval/approval_form.html",
        {"form": form, "approval": approval},
    )


class ApprovalDeleteView(LoginRequiredMixin, DeleteView):
    model = Approval
    success_url = reverse_lazy("approval:approval_approval_list")


@login_required
# create a list view for approvalline with status pending
def approvalline_list(request):
    approvallines = ApprovalLine.objects.exclude(status="Billed")
    filter = ApprovalLineFilter(request.GET, queryset=approvallines)
    return render(request, "approval/approvalline_list.html", {"filter": filter})


@login_required
def approvalline_create_update(request, approval_pk, pk=None):
    approval = get_object_or_404(Approval, pk=approval_pk)
    url = reverse(
        "approval:approval_approvalline_create", kwargs={"approval_pk": approval.pk}
    )
    line = None
    if pk:
        line = get_object_or_404(ApprovalLine, pk=pk)
        url = line.get_hx_edit_url()

    form = ApprovalLineForm(request.POST or None, instance=line)
    if request.method == "POST" and form.is_valid():
        approvalline = form.save(commit=False)
        approvalline.approval = approval
        approvalline.save()
        if request.htmx:
            return HttpResponse(status=204, headers={"HX-Trigger": "approvalChanged"})
        return redirect("approval:approval_approvalline_detail", pk=approvalline.pk)

    return render(
        request,
        "approval/approvalline_form.html",
        {"form": form, "approval": approval, "url": url, "line": line},
    )


@login_required
def approval_line_detail(request, pk):
    approvalline = get_object_or_404(ApprovalLine, pk=pk)
    return render(
        request,
        "approval/approvalline_detail.html",
        {
            "item": approvalline,
        },
    )


@login_required
def approvalline_delete(request, pk):
    approvalline = get_object_or_404(ApprovalLine, pk=pk)
    if request.method == "POST":
        approvalline.delete()
        if request.htmx:
            return HttpResponse(status=204, headers={"HX-Trigger": "approvalChanged"})
    raise Http404()


@login_required
def return_list(request):
    returns = Return.objects.all()
    return render(request, "approval/return_list.html", {"object_list": returns})


@login_required
def return_create(request):
    if request.method == "POST":
        form = ReturnForm(request.POST)
        if form.is_valid():
            ret = form.save(commit=False)
            ret.created_by = request.user
            ret.save()
            return redirect(ret)
    else:
        form = ReturnForm()
    return render(
        request,
        "approval/return_form.html",
        {"form": form},
    )


@login_required
@for_htmx(use_block="content")
def return_detail(request, pk):
    ret = get_object_or_404(Return, pk=pk)
    return TemplateResponse(
        request,
        "approval/return_detail.html",
        {
            "object": ret,
        },
    )


@login_required
def return_update(request, pk):
    ret = get_object_or_404(Return, pk=pk)
    if request.method == "POST":
        form = ReturnForm(request.POST, instance=ret)
        if form.is_valid():
            ret = form.save(commit=False)
            ret.save()
            return redirect(ret)
    else:
        form = ReturnForm(instance=ret)
    return render(request, "approval/return_form.html", {"form": form, "ret": ret})


class ReturnDeleteView(LoginRequiredMixin, DeleteView):
    model = Return
    success_url = reverse_lazy("approval:approval_return_list")


@login_required
def returnitem_create_update(request, return_pk, pk=None):
    ret = get_object_or_404(Return, pk=return_pk)
    retitem = None
    url = reverse("approval:approval_returnitem_create", kwargs={"return_pk": ret.pk})
    if pk:
        retitem = get_object_or_404(ReturnItem, pk=pk)
        url = retitem.get_hx_edit_url()

    form = ReturnItemForm(request.POST or None, instance=retitem,return_obj=ret)
    if request.method == "POST" and form.is_valid():
        retitem = form.save(commit=False)
        retitem.return_obj = ret
        retitem.save()
        if request.htmx:
            return HttpResponse(status=204, headers={"HX-Trigger": "returnChanged"})
        return redirect("approval:approval_returnitem_detail", pk=retitem.pk)

    return render(
        request,
        "approval/returnitem_form.html",
        {"form": form, "return_obj": ret, "line": retitem, "url": url},
    )


@login_required
def returnitem_delete(request, pk):
    retitem = get_object_or_404(ReturnItem, pk=pk)
    if request.method == "POST":
        retitem.delete()
        if request.htmx:
            return HttpResponse(status=204, headers={"HX-Trigger": "returnChanged"})
        return redirect(retitem.return_obj)
    return render(
        request,
        "approval/return_delete.html",
        {"object": retitem},
    )


@login_required
def returnitem_detail(request, pk):
    ret = get_object_or_404(ReturnItem, pk=pk)
    return render(
        request,
        "approval/returnline_detail.html",
        {
            "item": ret,
        },
    )
