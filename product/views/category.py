from utils.htmx_utils import for_htmx
from ..forms import CategoryForm
from ..models import Category
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404, redirect

@login_required
@for_htmx(use_block="content")
def category_list(request):
    categories = Category.objects.all()
    ctx = {"object_list": categories}
    return TemplateResponse(request, "product/category_list.html", ctx)

@login_required
@for_htmx(use_block="content")
def category_create(request):
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        category = form.save()
        return redirect("product_category_detail", slug=category.slug)
    ctx = {"form": form}
    return TemplateResponse(request, "product/category_form.html", ctx)

@login_required
@for_htmx(use_block="content")
def category_detail(request,slug):
    category = get_object_or_404(Category, slug=slug)
    ctx = {"object": category}
    return TemplateResponse(request, "product/category_detail.html", ctx)

@login_required
@for_htmx(use_block="content")
def category_update(request, slug):
    category = get_object_or_404(Category, slug=slug)
    form = CategoryForm(request.POST or None, instance=category)
    if form.is_valid():
        category = form.save()
        return redirect("product_category_detail", slug=category.slug)
    ctx = {"form": form, "category": category}
    return TemplateResponse(request, "product/category_form.html", ctx)
    
@login_required
def category_delete(request, slug):
    category = get_object_or_404(Category, slug=slug)
    category.delete()
    return redirect("product_category_list")