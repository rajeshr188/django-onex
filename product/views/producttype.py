from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from ..forms import ProductTypeForm
from ..models import ProductType
from utils.htmx_utils import for_htmx
from django.shortcuts import redirect,get_object_or_404

@login_required
@for_htmx(use_block="content")
def producttype_list(request):
    producttypes = ProductType.objects.all()
    ctx = {"object_list": producttypes}
    return TemplateResponse(request, "product/producttype_list.html", ctx)

@login_required
@for_htmx(use_block="content")
def producttype_create(request):
    form = ProductTypeForm(request.POST or None)
    if form.is_valid():
        producttype = form.save()
        return redirect("product_producttype_detail", pk=producttype.pk)
    ctx = {"form": form}
    return TemplateResponse(request, "product/producttype_form.html", ctx)

@login_required
@for_htmx(use_block="content")
def producttype_detail(request, pk):
    producttype = get_object_or_404(ProductType, pk=pk)
    ctx = {"object": producttype}
    return TemplateResponse(request, "product/producttype_detail.html", ctx)

@login_required
@for_htmx(use_block="content")
def producttype_update(request, pk):
    producttype = get_object_or_404(ProductType, pk=pk)
    form = ProductTypeForm(request.POST or None, instance=producttype)
    if form.is_valid():
        producttype = form.save()
        return redirect("product_producttype_detail", pk=producttype.pk)
    ctx = {"form": form, "producttype": producttype}
    return TemplateResponse(request, "product/producttype_form.html", ctx)

@login_required
def producttype_delete(request, pk):
    producttype = get_object_or_404(ProductType, pk=pk)
    producttype.delete()
    return redirect("product_producttype_list")
