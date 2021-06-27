import decimal
from django.views.generic import DetailView, ListView, UpdateView, CreateView, DeleteView
from .models import (Category, ProductType, Product, ProductVariant, Attribute,
                    AttributeValue, ProductImage, StockStatement, VariantImage,Stock,
                    StockTransaction)
from .forms import (CategoryForm, ProductTypeForm, ProductForm,
                    ProductVariantForm,AttributeForm, AttributeValueForm,
                     ProductImageForm, VariantImageForm,StockForm,UniqueForm,
                     StockTransactionForm)
from .filters import ProductFilter,ProductVariantFilter
from django.shortcuts import get_object_or_404,redirect
from django.urls import reverse,reverse_lazy
from django.template.response import TemplateResponse
from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
# from blabel import Labelwriter

class CategoryListView(LoginRequiredMixin,ListView):
    model = Category

class CategoryCreateView(LoginRequiredMixin,CreateView):
    model = Category
    form_class = CategoryForm

class CategoryDetailView(LoginRequiredMixin,DetailView):
    model = Category

class CategoryUpdateView(LoginRequiredMixin,UpdateView):
    model = Category
    form_class = CategoryForm

class ProductTypeListView(LoginRequiredMixin,ListView):
    model = ProductType

class ProductTypeCreateView(LoginRequiredMixin,CreateView):
    model = ProductType
    form_class = ProductTypeForm

class ProductTypeDetailView(LoginRequiredMixin,DetailView):
    model = ProductType

class ProductTypeDeleteView(LoginRequiredMixin,DeleteView):
    model = ProductType
    success_url = reverse_lazy('product_producttype_list')

class ProductTypeUpdateView(LoginRequiredMixin,UpdateView):
    model = ProductType
    form_class = ProductTypeForm

class ProductListView(LoginRequiredMixin,FilterView):
    model = Product
    filterset_class = ProductFilter
    template_name = 'product/product_list.html'

@login_required
def product_create(request, type_pk):
    track_inventory = True
    product_type = get_object_or_404(ProductType, pk=type_pk)
    create_variant = not product_type.has_variants
    product = Product()
    product.product_type = product_type
    product_form =ProductForm(request.POST or None, instance=product)
    if create_variant:
        variant = ProductVariant(
            product=product, track_inventory=track_inventory)
        variant_form = ProductVariantForm(
            request.POST or None,
            instance=variant, prefix='variant')
        variant_errors = not variant_form.is_valid()
    else:
        variant_form = None
        variant_errors = False

    if product_form.is_valid() and not variant_errors:
        product = product_form.save()
        if create_variant:
            variant.product = product
            variant_form.save()

        return redirect('product_product_detail', pk=product.pk)
    ctx = {
        'product_form': product_form, 'variant_form': variant_form,
        'product': product}
    return TemplateResponse(request, 'product/product_form.html', ctx)


class ProductDetailView(LoginRequiredMixin,DetailView):
    model = Product
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        products = Product.objects.prefetch_related('variants', 'images').all()
        product = get_object_or_404(products, pk=self.kwargs.pop('pk'))
        variants = product.variants.all()
        # Add in a QuerySet of all the books
        context['variants'] =variants
        return context

@login_required
def product_edit(request, pk):
    product = get_object_or_404(
        Product.objects.prefetch_related('variants'), pk=pk)
    form = ProductForm(request.POST or None, instance=product)

    edit_variant = not product.product_type.has_variants
    if edit_variant:
        variant = product.variants.first()
        variant_form = ProductVariantForm(
            request.POST or None, instance=variant, prefix='variant')
        variant_errors = not variant_form.is_valid()
    else:
        variant_form = None
        variant_errors = False

    if form.is_valid() and not variant_errors:
        product = form.save()
        if edit_variant:
            variant_form.save()
        return redirect('product_product_detail', pk=product.pk)
    ctx = {
        'product': product, 'product_form': form, 'variant_form': variant_form}
    return TemplateResponse(request, 'product/product_form.html', ctx)

class ProductDeleteView(LoginRequiredMixin,DeleteView):
    model = Product
    success_url = reverse_lazy('product_product_list')

class ProductVariantListView(LoginRequiredMixin,FilterView):
    model = ProductVariant
    filterset_class = ProductVariantFilter
    template_name = "product/productvariant_list.html"

@login_required
def variant_create(request, pk):
    track_inventory = True
    product = get_object_or_404(Product.objects.all(), pk=pk)
    variant = ProductVariant(product=product, track_inventory=track_inventory)
    form = ProductVariantForm(
        request.POST or None,
        instance=variant)
    if form.is_valid():
        form.save()
        return redirect(
            'product_productvariant_detail',
            pk=variant.pk)
    ctx = {'form': form, 'product': product, 'variant': variant}
    return TemplateResponse(
        request,
        'product/productvariant_form.html',
        ctx)

class ProductVariantDetailView(LoginRequiredMixin,DetailView):
    model = ProductVariant

class ProductVariantUpdateView(LoginRequiredMixin,UpdateView):
    model = ProductVariant
    form_class = ProductVariantForm

class ProductVariantDeleteView(LoginRequiredMixin,DeleteView):
    model = ProductVariant
    success_url = reverse_lazy('product_productvariant_list')

class AttributeListView(LoginRequiredMixin,ListView):
    model = Attribute

class AttributeCreateView(LoginRequiredMixin,CreateView):
    model = Attribute
    form_class = AttributeForm

class AttributeDetailView(LoginRequiredMixin,DetailView):
    model = Attribute

class AttributeUpdateView(LoginRequiredMixin,UpdateView):
    model = Attribute
    form_class = AttributeForm

class AttributeValueListView(LoginRequiredMixin,ListView):
    model = AttributeValue

class AttributeValueCreateView(LoginRequiredMixin,CreateView):
    model = AttributeValue
    form_class = AttributeValueForm

class AttributeValueDetailView(LoginRequiredMixin,DetailView):
    model = AttributeValue

class AttributeValueUpdateView(LoginRequiredMixin,UpdateView):
    model = AttributeValue
    form_class = AttributeValueForm

class ProductImageListView(LoginRequiredMixin,ListView):
    model = ProductImage

class ProductImageCreateView(LoginRequiredMixin,CreateView):
    model = ProductImage
    form_class = ProductImageForm

class ProductImageDetailView(LoginRequiredMixin,DetailView):
    model = ProductImage

class ProductImageUpdateView(LoginRequiredMixin,UpdateView):
    model = ProductImage
    form_class = ProductImageForm

class VariantImageListView(LoginRequiredMixin,ListView):
    model = VariantImage

class VariantImageCreateView(LoginRequiredMixin,CreateView):
    model = VariantImage
    form_class = VariantImageForm

class VariantImageDetailView(LoginRequiredMixin,DetailView):
    model = VariantImage

class VariantImageUpdateView(LoginRequiredMixin,UpdateView):
    model = VariantImage
    form_class = VariantImageForm

# def print_qr(self,request):
#     node = get_object_or_404(Stree,pk = pk)
#
#     label_writer = Labelwriter("product/item_qr_template.html",
#                                 default_stylesheets = ("style.css",))
#     records = [
#         dict(sample_id = node.barcode,sample_name=node.full_name)
#     ]
#     label_writer.write_labels(records,target='qrcode_and_date.pdf')

from django.shortcuts import render
from django.http import HttpResponseRedirect
from decimal import *
def split_lot(request,pk):
    # If this is a POST request then process the Form data
    stock = get_object_or_404(Stock,pk = pk)
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = UniqueForm(request.POST or None)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            print(form)
            print(form.cleaned_data)
            weight = form.cleaned_data['weight']
            stock.split(weight)

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('product_stock_list') )

    # If this is a GET (or any other method) create the default form.
    else:
        # form = UniqueForm(initial = {"parent":parent})
        form = UniqueForm(initial = {"stock":stock})

    context = {
        'form': form,
    }

    return render(request, 'product/split_lot.html', context)

def merge_lot(request,pk):
    node = Stock.objects.get(id=pk)
    print(f"to merge node{node}")
    node.merge()

    return HttpResponseRedirect(reverse('product_stock_list') )

class StockListView(ListView):
    model=Stock

class StockCreateView(CreateView):
    model=Stock
    form_class=StockForm

class StockUpdateView(UpdateView):
    model=Stock
    form_class=StockForm

class StockDetailView(DetailView):
    model=Stock

class StockDeleteView(DeleteView):
    model = Stock
    success_url = reverse_lazy('product_stock_list')

class StockTransactionCreateView(CreateView):
    model=StockTransaction
    form_class=StockTransactionForm

class StockTransactionListView(ListView):
    model=StockTransaction

class StockTransactionDetailView(DetailView):
    model=StockTransaction

class StockTransactionUpdateView(UpdateView):
    model=StockTransaction
    form_class=StockTransactionForm

class StockTransactionDeleteView(DeleteView):
    model = StockTransaction
    success_url = reverse_lazy('product_stocktransaction_list')

class StockStatementListView(ListView):
    model = StockStatement

def audit_stock(request):
    stocks = Stock.objects.all()
    for i in stocks:
        i.audit()
    return HttpResponseRedirect(reverse('product_stock_list'))
