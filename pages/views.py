import datetime

from actstream import action
from actstream.models import Action, actor_stream, any_stream, user_stream
from django.contrib.auth.decorators import login_required
from django.db.models import Count, FloatField, Sum
from django.db.models.functions import Cast, Coalesce
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView

from contact.models import Customer
from contact.services import (active_customers, get_customers_by_type,
                              get_customers_by_year)
from girvi.models import Loan
from girvi.services import *


@login_required
def HomePageView(request):
    return render(request, "pages/home.html")


class AboutPageView(TemplateView):
    template_name = "pages/about.html"


class PrivacyPolicy(TemplateView):
    template_name = "pages/privacy_policy.html"


class TermsAndConditions(TemplateView):
    template_name = "pages/terms_and_conditions.html"


@login_required
def Dashboard(request):
    context = {}
    # context['stream'] = user_stream(request.user, with_user_activity=True)
    # context['any_stream'] = any_stream(request.user)
    # context['actor_stream'] = actor_stream(request.user)
    # context['action'] = Action.objects.all()
    if request.user.is_superuser:
        # If the user is a superuser, get all actions.
        actions = Action.objects.all()
    else:
        # If the user is not a superuser, get only their actions.
        actions = user_stream(request.user)
    context["actions"] = actions
    action.send(request.user, verb="posted", target=request.user)

    # from purchase.models import Invoice as Pinv
    # from sales.models import Invoice as Sinv

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
    context["grouped_loan_counts"] = get_loan_counts_grouped()
    loan = Loan.objects.with_details()
    unreleased = loan.unreleased()
    sunken = unreleased.filter(is_overdue="True")

    context["loan_count"] = unreleased.count()

    context["due_amount"] = unreleased.aggregate(
        Sum("loan_amount"), Sum("total_interest"), Sum("total_due")
    )
    context["total_loan_amount"] = context["due_amount"]["loan_amount__sum"]
    context["total_interest"] = context["due_amount"]["total_interest__sum"]

    context[
        "assets"
    ] = unreleased.with_itemwise_loanamount().total_itemwise_loanamount()
    context["loanbyitemtype"] = get_loanamount_by_itemtype()
    context["weight"] = unreleased.total_weight()
    context["pure_weight"] = unreleased.total_pure_weight()

    context["current_value"] = unreleased.total_current_value()
    context["itemwise_value"] = unreleased.itemwise_value()
    context["total_current_value"] = unreleased.total_current_value()["total"]

    context["sunken"] = {}
    context["sunken"]["loan_count"] = sunken.count()
    context["sunken"]["total_loan_amount"] = sunken.total_loanamount()
    context["sunken"][
        "assets"
    ] = sunken.with_itemwise_loanamount().total_itemwise_loanamount()
    context["sunken"]["weight"] = sunken.total_weight()
    context["sunken"]["due_amount"] = sunken.aggregate(
        Sum("loan_amount"), Sum("total_interest"), Sum("total_due")
    )
    context["sunken"]["current_value"] = sunken.total_current_value()
    context["sunken"]["itemwise_value"] = sunken.itemwise_value()
    context["sunken"]["total_current_value"] = sunken.total_current_value()["total"]
    context["sunken"]["total_interest"] = sunken.aggregate(total=Sum("total_interest"))
    context["sunken"]["pure_weight"] = sunken.total_pure_weight()

    context["loan_progress"] = round(
        Loan.objects.released().count() / Loan.objects.count() * 100, 2
    )
    context["loan_data_by_year"] = get_loans_by_year()
    context["customer_data_by_year"] = get_customers_by_year()
    context["customer_data_by_type"] = get_customers_by_type()
    context["active_customers"] = active_customers()
    context["maxloans"] = (
        Customer.objects.filter(loan__release__isnull=True)
        .annotate(
            num_loans=Count("loan"),
            sum_loans=Sum("loan__loan_amount"),
            tint=Sum("loan__interest"),
        )
        .values("name", "num_loans", "sum_loans", "tint")
        .order_by("-num_loans", "sum_loans", "tint")
    )
    context["interest_received"] = get_interest_paid()
    return render(request, "pages/dashboard.html", context)
