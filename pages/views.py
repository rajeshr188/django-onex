import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Count, FloatField, Sum
from django.db.models.functions import Cast, Coalesce
from django.shortcuts import render
from django.views.generic import TemplateView

from contact.models import Customer
from girvi.models import Loan


@login_required
def HomePageView(request):
    return render(request, "pages/home.html")


class AboutPageView(TemplateView):
    template_name = "pages/about.html"


@login_required
def Dashboard(request):
    context = {}
    from purchase.models import Invoice as Pinv
    from sales.models import Invoice as Sinv

    # pinv = Pinv.objects
    # sinv = Sinv.objects
    # total_pbal = pinv.filter(balancetype="Gold").aggregate(
    #     net_wt=Coalesce(Cast(Sum("net_wt"), output_field=FloatField()), 0.0),
    #     gwt=Coalesce(Cast(Sum("gross_wt"), output_field=FloatField()), 0.0),
    #     bal=Coalesce(Cast(Sum("balance"), output_field=FloatField()), 0.0),
    # )
    # total_sbal = sinv.filter(balancetype="Gold").aggregate(
    #     net_wt=Coalesce(Cast(Sum("net_wt"), output_field=FloatField()), 0.0),
    #     gwt=Coalesce(Cast(Sum("gross_wt"), output_field=FloatField()), 0.0),
    #     bal=Coalesce(Cast(Sum("balance"), output_field=FloatField()), 0.0),
    # )
    # total_pbal_ratecut = pinv.filter(balancetype="Cash").aggregate(
    #     net_wt=Coalesce(Cast(Sum("net_wt"), output_field=FloatField()), 0.0),
    #     gwt=Coalesce(Cast(Sum("gross_wt"), output_field=FloatField()), 0.0),
    #     bal=Coalesce(Cast(Sum("balance"), output_field=FloatField()), 0.0),
    # )
    # total_sbal_ratecut = sinv.filter(balancetype="Cash").aggregate(
    #     net_wt=Coalesce(Cast(Sum("net_wt"), output_field=FloatField()), 0.0),
    #     gwt=Coalesce(Cast(Sum("gross_wt"), output_field=FloatField()), 0.0),
    #     bal=Coalesce(Cast(Sum("balance"), output_field=FloatField()), 0.0),
    # )
    # context["total_pbal"] = total_pbal
    # context["total_sbal"] = total_sbal
    # context["pbal"] = total_pbal["bal"] - total_sbal["bal"]
    # context["total_pbal_ratecut"] = total_pbal_ratecut
    # context["total_sbal_ratecut"] = total_sbal_ratecut
    # context["sbal"] = total_pbal_ratecut["bal"] - total_sbal_ratecut["bal"]
    # context["remaining_net_wt"] = (
    #     total_pbal_ratecut["net_wt"] - total_sbal_ratecut["net_wt"]
    # )
    # try:
    #     context["p_map"] = round(
    #         total_pbal_ratecut["bal"] / total_pbal_ratecut["net_wt"], 3
    #     )
    # except ZeroDivisionError:
    #     context["p_map"] = 0.0
    # context['s_map'] = round(total_sbal_ratecut['bal']/total_sbal_ratecut['net_wt'],3)

    context["customer_count"] = Customer.objects.values("customer_type").annotate(
        count=Count("id")
    )

    loan = Loan.objects.with_details()
    unreleased = loan.unreleased()
    sunken = unreleased.filter(is_overdue="True")

    context["unreleased"] = {}
    context["loan_count"] = unreleased.count()
    context["total_loan_amount"] = unreleased.total_loanamount()
    context[
        "assets"
    ] = unreleased.with_itemwise_loanamount().total_itemwise_loanamount()
    context["weight"] = unreleased.total_weight()
    context["due_amount"] = unreleased.aggregate(
        Sum("loanamount"), Sum("total_interest"), Sum("total_due")
    )
    context["current_value"] = unreleased.total_current_value()
    context["itemwise_value"] = unreleased.itemwise_value()
    context["total_current_value"] = unreleased.total_current_value()["total"]
    context["total_interest"] = unreleased.aggregate(total=Sum("total_interest"))
    context["pure_weight"] = unreleased.total_pure_weight()

    context["sunken"] = {}
    context["sunken"]["loan_count"] = sunken.count()
    context["sunken"]["total_loan_amount"] = sunken.total_loanamount()
    context["sunken"][
        "assets"
    ] = sunken.with_itemwise_loanamount().total_itemwise_loanamount()
    context["sunken"]["weight"] = sunken.total_weight()
    context["sunken"]["due_amount"] = sunken.aggregate(
        Sum("loanamount"), Sum("total_interest"), Sum("total_due")
    )
    context["sunken"]["current_value"] = sunken.total_current_value()
    context["sunken"]["itemwise_value"] = sunken.itemwise_value()
    context["sunken"]["total_current_value"] = sunken.total_current_value()["total"]
    context["sunken"]["total_interest"] = sunken.aggregate(total=Sum("total_interest"))
    context["sunken"]["pure_weight"] = sunken.total_pure_weight()

    context["loan_progress"] = round(
        Loan.objects.released().count() / Loan.objects.count() * 100, 2
    )

    # context["is_overdue"] = (
    #     unreleased.with_details().filter(is_overdue=True)
    # )
    # context["sunken_count"] = context["is_overdue"].count()
    # context["sunken_total"] = context["is_overdue"].aggregate(Sum("total_due"))["total_due__sum"]

    return render(request, "pages/dashboard.html", context)
