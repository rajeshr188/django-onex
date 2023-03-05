from datetime import datetime, timedelta
import base64
from django.core.files.base import ContentFile
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django_tables2.config import RequestConfig
from render_block import render_block_to_string
from django.views.decorators.http import require_http_methods  # new

from sales.models import Month

from .filters import CustomerFilter
from .forms import CustomerForm,ContactForm,AddressForm
from .models import Customer,Contact,Address,Proof
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
def customer_list(request):
    context = {}
    f = CustomerFilter(request.GET, queryset=Customer.objects.all())
    table = CustomerTable(f.qs)
    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    context["filter"] = f
    context["table"] = table

    if request.htmx:
        response = render_block_to_string(
            "contact/customer_list.html", "content", context, request
        )
        return HttpResponse(response)
    return render(request, "contact/customer_list.html", context)


@require_http_methods(["DELETE"])
def customer_delete(request, pk):
    Customer.objects.filter(id=pk).delete()
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

            # messages.success(request, f"created customer {f}")
            # table = CustomerTable(data=Customer.objects.all())
            # table.paginate(page=request.GET.get("page", 1), per_page=10)
            # context = {"filter": CustomerFilter, "table": table}

            # response = render_block_to_string("contact/customer_list.html",'content',context,request)
            # return HttpResponse(response)
            return redirect("contact_customer_list")

        else:
            print("form invalid")
            messages.error(request, f"Error creating customer")
            return render(request, "contact/customer_form.html", {"form": form})

    else:
        form = CustomerForm()

        if request.htmx:
            response = render_block_to_string(
                "contact/customer_form.html", "content", {"form": form}, request
            )
            return HttpResponse(response)

        return render(request, "contact/customer_form.html", {"form": form})


@login_required
def customer_detail(request, pk=None):
    context = {}
    cust = get_object_or_404(Customer, pk=pk)
    data = cust.sales.all()
    inv = data.exclude(status="Paid")
    how_many_days = 30
    context["object"] = cust
    context["customer"] = cust
    context["current"] = inv.filter(
        created__gte=datetime.now() - timedelta(days=how_many_days)
    ).aggregate(
        tc=Sum("balance", filter=Q(balancetype="Cash")),
        tm=Sum("balance", filter=Q(balancetype="Gold")),
    )
    context["past"] = inv.filter(
        created__lte=datetime.now() - timedelta(days=how_many_days)
    ).aggregate(
        tc=Sum("balance", filter=Q(balancetype="Cash")),
        tm=Sum("balance", filter=Q(balancetype="Gold")),
    )
    context["monthwise"] = (
        inv.annotate(month=Month("created"))
        .values("month")
        .order_by("month")
        .annotate(
            tc=Sum("balance", filter=Q(balancetype="Cash")),
            tm=Sum("balance", filter=Q(balancetype="Gold")),
        )
        .values("month", "tm", "tc")
    )
    context["monthwiserev"] = (
        data.annotate(month=Month("created"))
        .values("month")
        .order_by("month")
        .annotate(
            tc=Sum("balance", filter=Q(balancetype="Cash")),
            tm=Sum("balance", filter=Q(balancetype="Gold")),
        )
        .values("month", "tm", "tc")
    )

    if request.htmx:
        response = render_block_to_string(
            "contact/customer_detail.html", "content", context, request
        )
        return HttpResponse(response)
    else:
        return render(request, "contact/customer_detail.html", context)


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
        messages.success(request, f"updated customer {f}")

        return redirect("contact_customer_list")

    return render(
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
def contact_create(request,pk = None):
    
    customer= get_object_or_404(Customer,pk=pk)
    form = ContactForm(request.POST or None)

    if request.method == 'POST':
        print("in post")
        if form.is_valid():
            print("form is valid")
            contact= form.save(commit=False)
            contact.Customer = customer
            print(f"contact:{contact}")
            contact.save()
            return render(request,'contact/contact_detail.html',context={'i':contact})
        else:
            return render(request,'contact/partials/contact_form.html',context={'form':form,'customer':customer})
   
    return render(request,'contact/partials/contact_form.html',context={'form':form,'customer':customer})

@login_required
def contact_detail(request,pk):
    contact = get_object_or_404(Contact,pk=pk)
    return render(request,'contact/contact_detail.html',context = {'i':contact})

@login_required
def contact_update(request,pk):
    contact = get_object_or_404(Contact,pk = pk)
    form = ContactForm(request.POST or None,instance = contact)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return render(request,'contact/contact_detail.html',context={'i':contact})
    return render(request,'contact/partials/contact_update_form.html',context = {'form':form,'contact':contact})

@login_required
@require_http_methods(["DELETE"])
def contact_delete(request,pk):
    contact = get_object_or_404(Contact,pk=pk)
    contact.delete()
    return HttpResponse('')

@login_required
def address_create(request,pk = None):
    
    customer= get_object_or_404(Customer,pk=pk)
    form = AddressForm(request.POST or None)

    if request.method == 'POST':
        print("in post")
        if form.is_valid():
            print("form is valid")
            address= form.save(commit=False)
            address.Customer = customer
            
            address.save()
            return render(request,'contact/address_detail.html',context={'i':address})
        else:
            return render(request,'contact/partials/address_form.html',context={'form':form,'customer':customer})
   
    return render(request,'contact/partials/address_form.html',context={'form':form,'customer':customer})

@login_required
def address_detail(request,pk):
    address = get_object_or_404(Address,pk=pk)
    return render(request,'contact/address_detail.html',context = {'i':address})


@login_required
def address_update(request,pk):
    address = get_object_or_404(Address,pk = pk)
    form = AddressForm(request.POST or None,instance = address)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return render(request,'contact/address_detail.html',context={'i':address})
    return render(request,'contact/partials/address_update_form.html',context = {'form':form,'address':address})

@login_required
@require_http_methods(["DELETE"])
def address_delete(request,pk):
    address = get_object_or_404(Address,pk=pk)
    address.delete()
    return HttpResponse('')
