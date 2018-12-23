from django.views.generic import DetailView, ListView, UpdateView, CreateView
from .models import Category, ProductType, Product, ProductVariant, Attribute, AttributeValue, ProductImage, VariantImage,Stock,StockTransaction
from .forms import CategoryForm, ProductTypeForm, ProductForm, ProductVariantForm, AttributeForm, AttributeValueForm, ProductImageForm, VariantImageForm,StockForm,StockTransactionForm
from django.shortcuts import get_object_or_404,redirect,reverse
from django.template.response import TemplateResponse
class CategoryListView(ListView):
    model = Category


class CategoryCreateView(CreateView):
    model = Category
    form_class = CategoryForm


class CategoryDetailView(DetailView):
    model = Category


class CategoryUpdateView(UpdateView):
    model = Category
    form_class = CategoryForm


class ProductTypeListView(ListView):
    model = ProductType


class ProductTypeCreateView(CreateView):
    model = ProductType
    form_class = ProductTypeForm


class ProductTypeDetailView(DetailView):
    model = ProductType


class ProductTypeUpdateView(UpdateView):
    model = ProductType
    form_class = ProductTypeForm


class ProductListView(ListView):
    model = Product

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


class ProductDetailView(DetailView):
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


class ProductVariantListView(ListView):
    model = ProductVariant


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

class ProductVariantDetailView(DetailView):
    model = ProductVariant


class ProductVariantUpdateView(UpdateView):
    model = ProductVariant
    form_class = ProductVariantForm


class AttributeListView(ListView):
    model = Attribute


class AttributeCreateView(CreateView):
    model = Attribute
    form_class = AttributeForm


class AttributeDetailView(DetailView):
    model = Attribute


class AttributeUpdateView(UpdateView):
    model = Attribute
    form_class = AttributeForm


class AttributeValueListView(ListView):
    model = AttributeValue


class AttributeValueCreateView(CreateView):
    model = AttributeValue
    form_class = AttributeValueForm


class AttributeValueDetailView(DetailView):
    model = AttributeValue


class AttributeValueUpdateView(UpdateView):
    model = AttributeValue
    form_class = AttributeValueForm


class ProductImageListView(ListView):
    model = ProductImage


class ProductImageCreateView(CreateView):
    model = ProductImage
    form_class = ProductImageForm


class ProductImageDetailView(DetailView):
    model = ProductImage


class ProductImageUpdateView(UpdateView):
    model = ProductImage
    form_class = ProductImageForm


class VariantImageListView(ListView):
    model = VariantImage


class VariantImageCreateView(CreateView):
    model = VariantImage
    form_class = VariantImageForm


class VariantImageDetailView(DetailView):
    model = VariantImage


class VariantImageUpdateView(UpdateView):
    model = VariantImage
    form_class = VariantImageForm

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
