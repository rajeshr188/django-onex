from django.views.generic import DetailView, ListView, UpdateView, CreateView, DeleteView
from django.views.generic.base import TemplateView
from .models import *
from .forms import *
from .filters import ProductFilter,ProductVariantFilter,StockFilter
from django.shortcuts import get_object_or_404,redirect, render
from django.urls import reverse_lazy
from django.template.response import TemplateResponse
from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
import logging

logger = logging.getLogger(__name__)
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

    product = get_object_or_404(Product.objects.all(), pk=pk)
    variant = ProductVariant(product=product)
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

def split_lot(request,pk):
    stock = get_object_or_404(Stock,pk = pk)
    if request.method == 'POST':
        form = UniqueForm(request.POST or None)
        if form.is_valid():
            weight = form.cleaned_data['weight']
            stock.split(weight)
            return reverse_lazy('product_stock_list')
    else:
        form = UniqueForm(initial = {"stock":stock})
    context = {'form': form,}

    return render(request, 'product/split_lot.html', context)

def merge_lot(request,pk):
    node = Stock.objects.get(id=pk)
    print(f"to merge node{node}")
    node.merge()
    return reverse_lazy('product_stock_list')

def stock_list(request):
    context = {}
    st = StockBalance.objects.all().select_related('stock','stock__variant')
    stock_filter = StockFilter(request.GET,queryset = st)
    # stock = []
    # for i in stock_filter.qs:
    #     bal ={}
    #     try:
    #         ls = i.stockstatement_set.latest()
    #         cwt = ls.Closing_wt
    #         cqty = ls.Closing_qty
    #     except StockStatement.DoesNotExist:
    #         ls = None
    #         cwt = 0
    #         cqty=0
    #     in_txns = i.stock_in_txns(ls)
    #     out_txns = i.stock_out_txns(ls)
    #     bal['wt'] = cwt + (in_txns['wt'] - out_txns['wt'])
    #     bal['qty'] = cqty + (in_txns['qty'] - out_txns['qty'])
    #     stock.append([i,bal])
    # context['stock']=stock
    return render(request,'product/stock_list.html',{'filter':stock_filter,
    # 'data':context
    }
    )

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

class StockStatementView(TemplateView):
    template_name = "product/add_stockstatement.html"

    def get(self,*args,**kwargs):
        formset = stockstatement_formset(queryset = StockStatement.objects.none())
        return self.render_to_response({'stockstatement_formset': formset})

    def post(self, *args, **kwargs):
        formset =stockstatement_formset(data=self.request.POST)
        if formset.is_valid():
            formset.save()
            return redirect(reverse_lazy("stockstatement_list"))

        return self.render_to_response({'stockstatement_formset': formset})

class StockBatchListView(ListView):
    model = StockBatch
class StockBatchDetailView(DetailView):
    model = StockBatch
def audit_stock(request):
    stocks = Stock.objects.all()
    for i in stocks:
        i.audit()
    return redirect('product_stock_list')

def inventory(request):
    inv = {}
    
    
    return render(request,'product/inventory.html',context = {})