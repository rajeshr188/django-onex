import base64
from datetime import datetime, timedelta
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_http_methods  # new
from django_tables2.config import RequestConfig
from render_block import render_block_to_string

from sales.models import Month
from utils.htmx_utils import for_htmx

from .filters import CustomerFilter
from .forms import AddressForm, ContactForm, CustomerForm, CustomerMergeForm
from .models import Address, Contact, Customer, Proof
from .tables import CustomerTable


@login_required
def home(request):
    data = dict()
    c = Customer.objects
    data["retailcount"] = c.filter(type="Re").count()

    data["wol"] = c.filter(type="Re", loan=None).count()
    data["wl"] = data["retailcount"] - data["wol"]
    data["customercount"] = c.all().count()

    data["whcount"] = c.filter(type="Wh").count()
    data["withph"] = round((c.exclude(phonenumber="911").count() / c.count()) * 100, 2)

    return render(
        request,
        "contact/home.html",
        context={"data": data},
    )


@login_required
@for_htmx(use_block="content")
# @for_htmx(use_block_from_params=True)
def customer_list(request):
    context = {}
    f = CustomerFilter(
        request.GET,
        queryset=Customer.objects.all().prefetch_related("contactno", "address"),
    )
    table = CustomerTable(f.qs)
    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    context["filter"] = f
    context["table"] = table

    return TemplateResponse(request, "contact/customer_list.html", context)


@require_http_methods(["DELETE"])
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    print(customer)
    messages.success(request, messages.DEBUG, f"Deleted customer {customer.name}")
    customer.delete()
    return HttpResponse("")


@login_required
def customer_create(request):
    if request.method == "POST":
        form = CustomerForm(request.POST or None, request.FILES)

        if form.is_valid():
            f = form.save(commit=False)
            f.created_by = request.user
            image_data = request.POST.get("image_data")

            if image_data:
                image_file = ContentFile(
                    base64.b64decode(image_data.split(",")[1]),
                    name=f"{f.name}_{f.relatedto}.jpg",
                )

                f.pic = image_file

            f.save()

            messages.success(request, messages.SUCCESS, f"created customer {f.name}")
            if "add" in request.POST:
                response = render_block_to_string(
                    "contact/customer_form.html",
                    "content",
                    {"form": CustomerForm()},
                    request,
                )
                return HttpResponse(
                    response,
                    headers={"Hx-Push-Url": reverse("contact_customer_create")},
                )

            else:
                response = render_block_to_string(
                    "contact/customer_detail.html",
                    "content",
                    {"customer": f, "object": f},
                    request,
                )
                return HttpResponse(
                    response,
                    headers={
                        "Hx-Push-Url": reverse(
                            "contact_customer_detail", kwargs={"pk": f.id}
                        )
                    },
                )
        else:
            messages.error(request, f"Error creating customer")
            return TemplateResponse(
                request, "contact/customer_form.html", {"form": form}
            )

    else:
        form = CustomerForm()

        if request.htmx:
            response = render_block_to_string(
                "contact/customer_form.html", "content", {"form": form}, request
            )
            return HttpResponse(response)

        return TemplateResponse(request, "contact/customer_form.html", {"form": form})


@login_required
@for_htmx(use_block="content")
def customer_merge(request):
    form = CustomerMergeForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            # merge logic
            original = form.cleaned_data["original"]
            duplicate = form.cleaned_data["duplicate"]
            original.merge(duplicate)
            return HttpResponseRedirect("contact_customer_list")
    return TemplateResponse(
        request, "contact/customer_merge.html", context={"form": form}
    )


@for_htmx(use_block="content")
@login_required
def customer_detail(request, pk=None):
    context = {}
    cust = get_object_or_404(Customer, pk=pk)
    # data = cust.sales.all()
    # inv = data.exclude(status="Paid")
    # how_many_days = 30
    context["object"] = cust
    context["customer"] = cust
    return TemplateResponse(request, "contact/customer_detail.html", context)


@for_htmx(use_block="content")
@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)

    if form.is_valid():
        f = form.save(commit=False)
        f.created_by = request.user
        image_data = request.POST.get("image_data")

        if image_data:
            image_file = ContentFile(
                base64.b64decode(image_data.split(",")[1]),
                name=f"{f.name}_{f.relatedas.replace('/','-')}_{f.relatedto}.jpg",
            )

            f.pic = image_file

        f.save()
        messages.success(request, messages.SUCCESS, f"updated customer {f}")

        return TemplateResponse(
            request, "contact/customer_detail.html", {"customer": f, "object": f}
        )

    return TemplateResponse(
        request, "contact/customer_form.html", {"form": form, "customer": customer}
    )


@login_required
def reallot_receipts(request, pk):
    customer = Customer.objects.get(pk=pk)
    customer.reallot_receipts()
    return redirect(customer.get_absolute_url())


@login_required
def reallot_payments(request, pk):
    customer = Customer.objects.get(pk=pk)
    customer.reallot_payments()
    return redirect(customer.get_absolute_url())


@login_required
def contact_create(request, pk=None):
    customer = get_object_or_404(Customer, pk=pk)
    form = ContactForm(request.POST or None, initial={"customer": customer})

    if request.method == "POST" and form.is_valid():
        f = form.save(commit=False)
        f.customer = customer
        f.save()

        return HttpResponse(status=204, headers={"HX-Trigger": "listChanged"})
        # return HttpResponse(status=204, headers={"HX-Redirect": reverse("contact_customer_list")})

    return render(
        request,
        "contact/partials/contact_form.html",
        context={"form": form, "customer": customer},
    )


@login_required
def contact_list(request, pk: int = None):
    print(f"called")
    customer = get_object_or_404(Customer, id=pk)
    contacts = customer.contactno.all()
    return render(
        request,
        "contact/contact_list.html",
        {"contacts": contacts, "customer_id": customer.id},
    )


@login_required
def address_list(request, pk: int = None):
    print(f"called")
    customer = get_object_or_404(Customer, id=pk)
    addresses = customer.address.all()
    return render(
        request,
        "contact/address_list.html",
        {"addresses": addresses, "customer_id": customer.id},
    )


@login_required
def contact_detail(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    return render(request, "contact/contact_detail.html", context={"i": contact})


@login_required
def contact_update(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    form = ContactForm(request.POST or None, instance=contact)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return render(
                request, "contact/contact_detail.html", context={"i": contact}
            )
    return render(
        request,
        "contact/partials/contact_update_form.html",
        context={"form": form, "contact": contact},
    )


@login_required
@require_http_methods(["DELETE"])
def contact_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    contact.delete()
    return HttpResponse(status=204, headers={"HX-Trigger": "listChanged"})


@login_required
def address_create(request, pk=None):
    customer = get_object_or_404(Customer, pk=pk)
    form = AddressForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        address = form.save(commit=False)
        address.Customer = customer

        address.save()
        return HttpResponse(status=204, headers={"HX-Trigger": "listChanged"})

    return render(
        request,
        "contact/partials/address_form.html",
        context={"form": form, "customer": customer},
    )


@login_required
def address_detail(request, pk):
    address = get_object_or_404(Address, pk=pk)
    return render(request, "contact/address_detail.html", context={"i": address})


@login_required
def address_update(request, pk):
    address = get_object_or_404(Address, pk=pk)
    form = AddressForm(request.POST or None, instance=address)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return render(
                request, "contact/address_detail.html", context={"i": address}
            )
    return render(
        request,
        "contact/partials/address_update_form.html",
        context={"form": form, "address": address},
    )


@login_required
@require_http_methods(["DELETE"])
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk)
    address.delete()
    return HttpResponse("")
