from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.http.response import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from dea.models import Journal
from utils.htmx_utils import for_htmx

from .filters import ApprovalLineFilter
from .forms import ApprovalForm, ApprovalLineForm, ReturnForm, ReturnItemForm
from .models import Approval, ApprovalLine, Return, ReturnItem


# Create your views here.
@transaction.atomic
def post_approval(request, pk):
    approval = get_object_or_404(Approval, pk=pk)
    approval.post()
    return redirect(approval)


@transaction.atomic
def unpost_approval(request, pk):
    approval = get_object_or_404(Approval, pk=pk)
    approval.unpost()
    return redirect(approval)


from invoice.models import PaymentTerm
from sales.models import Invoice as sinv
from sales.models import InvoiceItem as sinvitem


@transaction.atomic()
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
def approval_list(request):
    approvals = Approval.objects.all()
    return render(request, "approval/approval_list.html", {"object_list": approvals})


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


@login_required
def approval_delete(request, pk):
    approval = get_object_or_404(Approval, pk=pk)
    if request.method == "POST":
        approval.delete()
        return redirect("approval:approval_list")
    return render(request, "approval/approval_delete.html", {"object": approval})


@login_required
def approvalline_create_update(request, approval_pk, pk=None):
    approval = get_object_or_404(Approval, pk=approval_pk)
    url = reverse("approval:approval_approvalline_create", kwargs={"approval_pk": approval.pk})
    line = None
    if pk:
        line = get_object_or_404(ApprovalLine, pk=pk)
        url = line.get_hx_edit_url()
        
    print(f"approval_pk: {approval_pk}, pk: {pk}, line: {line}")
    form = ApprovalLineForm(request.POST or None, instance=line)
    if request.method == "POST":
        
        if form.is_valid():
            approvalline = form.save(commit=False)
            approvalline.approval = approval
            approvalline.save()
            if request.htmx:
                return HttpResponse(
                    status=204, headers={"HX-Trigger": "approvalChanged"}
                )
            return redirect("approval:approval_approvalline_detail", pk=approvalline.pk)
    
    return render(
        request,
        "approval/approvalline_form.html",
        {"form": form, "approval": approval,"url":url,"line":line},
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
def return_create(request, pk):
    approval = get_object_or_404(Approval, pk=pk)
    if request.method == "POST":
        form = ReturnForm(request.POST)
        if form.is_valid():
            ret = form.save(commit=False)
            ret.approval = approval
            ret.save()
            return redirect(ret)
    else:
        form = ReturnForm()
    return render(
        request,
        "approval/return_form.html",
        {"form": form, "approval": approval},
    )


@login_required
def return_detail(request, pk):
    ret = get_object_or_404(Return, pk=pk)
    return render(
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


@login_required
def return_delete(request, pk):
    ret = get_object_or_404(Return, pk=pk)
    if request.method == "POST":
        ret.delete()
        return redirect(ret.approval)
    return render(request, "approval/return_delete.html", {"object": ret})


# create fbv for returnitem_create
@login_required
def returnitem_create(request, pk):
    ret = get_object_or_404(Return, pk=pk)
    if request.method == "POST":
        form = ReturnForm(request.POST)
        if form.is_valid():
            retitem = form.save(commit=False)
            retitem.return_obj = ret
            retitem.save()
            return redirect(retitem)
    else:
        form = ReturnForm()
    return render(
        request,
        "approval/return_form.html",
        {"form": form, "return_obj": ret},
    )


# create fbv for returnitem_update
@login_required
def returnitem_update(request, pk):
    retitem = get_object_or_404(ReturnItem, pk=pk)
    if request.method == "POST":
        form = ReturnForm(request.POST, instance=retitem)
        if form.is_valid():
            retitem = form.save(commit=False)
            retitem.save()
            return redirect(retitem.return_obj)
    else:
        form = ReturnForm(instance=retitem)
    return render(
        request,
        "approval/return_form.html",
        {"form": form, "retitem": retitem},
    )


@login_required
def returnitem_delete(request, pk):
    retitem = get_object_or_404(ReturnItem, pk=pk)
    if request.method == "POST":
        retitem.delete()
        return redirect(retitem.return_obj)
    return render(
        request,
        "approval/return_delete.html",
        {"object": retitem},
    )
