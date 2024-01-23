import base64
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods  # new
from django_tables2.config import RequestConfig

from utils.htmx_utils import for_htmx

from .filters import CustomerFilter
from .forms import (AddressForm, ContactForm, CustomerForm, CustomerMergeForm,
                    CustomerRelationshipForm)
from .models import Address, Contact, Customer, CustomerRelationship, Proof
from .tables import CustomerTable


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
    customer.delete()
    messages.success(request, messages.DEBUG, f"Deleted customer {customer.name}")
    return HttpResponse("")


@login_required
@for_htmx(use_block="content")
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
                    name=f"{f.name}_{f.relatedas.replace('/','-')}_{f.relatedto}_{f.id}.jpg",
                )

                f.pic = image_file

            f.save()

            messages.success(request, messages.SUCCESS, f"created customer {f.name}")
            if "add" in request.POST:
                response = TemplateResponse(
                    request, "contact/customer_form.html", {"form": CustomerForm()}
                )
                response["HX-Push-Url"] = reverse("contact_customer_create")
                return response

            else:
                response = TemplateResponse(
                    request,
                    "contact/customer_detail.html",
                    {"customer": f, "object": f},
                )
                response["HX-Push-Url"] = reverse(
                    "contact_customer_detail", kwargs={"pk": f.id}
                )
                return response
        else:
            messages.error(request, f"Error creating customer")
            return TemplateResponse(
                request, "contact/customer_form.html", {"form": form}
            )

    else:
        form = CustomerForm()
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
            return redirect("contact_customer_list")
    return TemplateResponse(
        request, "contact/customer_merge.html", context={"form": form}
    )


@for_htmx(use_block="content")
@login_required
def customer_detail(request, pk=None):
    context = {}
    cust = get_object_or_404(Customer, pk=pk)
    context["object"] = cust
    context["customer"] = cust
    loans = cust.loan_set.unreleased().with_details()
    for i in loans:
        print(f"get_worth:{i.get_worth} | worth: {i.worth}")
    worth = [i.worth for i in loans]
    context["worth"] = sum(worth)
    return TemplateResponse(request, "contact/customer_detail.html", context)


@login_required
def create_relationship(request, from_customer_id):
    from_customer = get_object_or_404(Customer, pk=from_customer_id)

    if request.method == "POST":
        form = CustomerRelationshipForm(request.POST, customer_id=from_customer)
        if form.is_valid():
            print(form.cleaned_data)
            print(form.errors)
            related_customer = form.cleaned_data["related_customer"]
            relationship = form.cleaned_data["relationship"]

            # Create a new CustomerRelationship instance
            CustomerRelationship.objects.create(
                customer=from_customer,
                relationship=relationship,
                related_customer=related_customer,
            )

            return redirect("contact_customer_detail", pk=from_customer_id)

    else:
        form = CustomerRelationshipForm(customer_id=from_customer)

    return render(
        request,
        "contact/create_relationship.html",
        {"form": form, "customer": from_customer},
    )


@login_required
@for_htmx(use_block="content")
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
                name=f"{f.name}_{f.relatedas.replace('/','-')}_{f.relatedto}_{f.id}.jpg",
            )

            f.pic = image_file

        f.save()
        messages.success(request, messages.SUCCESS, f"updated customer {f}")

        response = TemplateResponse(
            request,
            "contact/customer_detail.html",
            {"customer": customer, "object": customer},
        )
        response["HX-Push-Url"] = reverse(
            "contact_customer_detail", kwargs={"pk": customer.id}
        )
        return response

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
