from django.db.models import Count, FloatField, Sum
from django.db.models.functions import Cast, Coalesce
from django.shortcuts import render
from django.views.generic import TemplateView

from contact.models import Customer
from girvi.models import Loan


class HomePageView(TemplateView):
    template_name = "pages/home.html"


class AboutPageView(TemplateView):
    template_name = "pages/about.html"


def Dashboard(request):
    context = {}
    from purchase.models import Invoice as Pinv
    from sales.models import Invoice as Sinv

    pinv = Pinv.objects
    sinv = Sinv.objects

    total_pbal = pinv.filter(balancetype="Gold").aggregate(
        net_wt=Coalesce(Cast(Sum("net_wt"), output_field=FloatField()), 0.0),
        gwt=Coalesce(Cast(Sum("gross_wt"), output_field=FloatField()), 0.0),
        bal=Coalesce(Cast(Sum("balance"), output_field=FloatField()), 0.0),
    )
    total_sbal = sinv.filter(balancetype="Gold").aggregate(
        net_wt=Coalesce(Cast(Sum("net_wt"), output_field=FloatField()), 0.0),
        gwt=Coalesce(Cast(Sum("gross_wt"), output_field=FloatField()), 0.0),
        bal=Coalesce(Cast(Sum("balance"), output_field=FloatField()), 0.0),
    )

    total_pbal_ratecut = pinv.filter(balancetype="Cash").aggregate(
        net_wt=Coalesce(Cast(Sum("net_wt"), output_field=FloatField()), 0.0),
        gwt=Coalesce(Cast(Sum("gross_wt"), output_field=FloatField()), 0.0),
        bal=Coalesce(Cast(Sum("balance"), output_field=FloatField()), 0.0),
    )
    total_sbal_ratecut = sinv.filter(balancetype="Cash").aggregate(
        net_wt=Coalesce(Cast(Sum("net_wt"), output_field=FloatField()), 0.0),
        gwt=Coalesce(Cast(Sum("gross_wt"), output_field=FloatField()), 0.0),
        bal=Coalesce(Cast(Sum("balance"), output_field=FloatField()), 0.0),
    )

    context["total_pbal"] = total_pbal
    context["total_sbal"] = total_sbal
    context["pbal"] = total_pbal["bal"] - total_sbal["bal"]
    context["total_pbal_ratecut"] = total_pbal_ratecut
    context["total_sbal_ratecut"] = total_sbal_ratecut
    context["sbal"] = total_pbal_ratecut["bal"] - total_sbal_ratecut["bal"]
    context["remaining_net_wt"] = (
        total_pbal_ratecut["net_wt"] - total_sbal_ratecut["net_wt"]
    )
    try:
        context["p_map"] = round(
            total_pbal_ratecut["bal"] / total_pbal_ratecut["net_wt"], 3
        )
    except ZeroDivisionError:
        context["p_map"] = 0.0

    # context['s_map'] = round(total_sbal_ratecut['bal']/total_sbal_ratecut['net_wt'],3)

    context["customer_count"] = Customer.objects.values("customer_type").annotate(
        count=Count("id")
    )
    context["loan"] = Loan.objects
    return render(request, "pages/dashboard.html", context)
