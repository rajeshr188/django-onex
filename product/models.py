import datetime
from decimal import Decimal
from django_extensions.db.fields import AutoSlugField
from django.conf import settings
from django.contrib.postgres.fields import HStoreField
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q,Sum
from django.urls import reverse
from django.utils.encoding import smart_text
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from django_measurement.models import MeasurementField
from measurement.measures import Weight
from mptt.managers import TreeManager
from mptt.models import MPTTModel
from versatileimagefield.fields import PPOIField, VersatileImageField
from .weight import WeightUnits, zero_weight
from django.contrib.contenttypes.fields import GenericForeignKey,GenericRelation
from django.contrib.contenttypes.models import ContentType

class Category(MPTTModel):
    # mens/womens/kids/uni
    name = models.CharField(max_length=128,unique=True)
    slug = AutoSlugField(populate_from='name', blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children',
        on_delete=models.CASCADE)
    background_image = VersatileImageField(
        upload_to='category-backgrounds', blank=True, null=True)

    objects = models.Manager()
    tree = TreeManager()

    class Meta:
        ordering = ('-pk',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_category_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('product_category_update', args=(self.slug,))

class ProductType(models.Model):
    # ring,bracelet,chain,necklace,harem,dollar,urupudi,coin,kalkas,moppu,mugti,kamal,tops,kassaset,jhapaka,mattal
    name = models.CharField(max_length=128)
    has_variants = models.BooleanField(default=True)
    product_attributes = models.ManyToManyField(
        'Attribute', related_name='product_types', blank=True)
    variant_attributes = models.ManyToManyField(
        'Attribute', related_name='product_variant_types', blank=True)

    class Meta:
        # app_label = 'product'
        ordering=('name',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_producttype_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('product_producttype_update', args=(self.pk,))

    def __repr__(self):
        class_ = type(self)
        return '<%s.%s(pk=%r, name=%r)>' % (
            class_.__module__, class_.__name__, self.pk, self.name)


class Product(models.Model):
    # tv ring,plate ring,dc chain,gc chain
    product_type = models.ForeignKey(
        ProductType, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    description = models.TextField()
    category = models.ForeignKey(
        Category, related_name='products', on_delete=models.CASCADE)
    attributes = HStoreField(default=dict, blank=True)

    class Meta:
        app_label = 'product'

    def __iter__(self):
        if not hasattr(self, '__variants'):
            setattr(self, '__variants', self.variants.all())
        return iter(getattr(self, '__variants'))

    def __repr__(self):
        class_ = type(self)
        return '<%s.%s(pk=%r, name=%r)>' % (
            class_.__module__, class_.__name__, self.pk, self.name)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_product_detail', args=(self.pk,))


    def get_update_url(self):
        return reverse('product_product_update', args=(self.pk,))


    def get_slug(self):
        return slugify(smart_text(unidecode(self.name)))

    def is_in_stock(self):
        return any(variant.is_in_stock() for variant in self)

    def get_first_image(self):
        images = list(self.images.all())
        return images[0].image if images else None

class ProductVariant(models.Model):
    sku = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255, blank=True)

    product = models.ForeignKey(
        Product, related_name='variants', on_delete=models.CASCADE)
    attributes = HStoreField(default=dict, blank=True)
    images = models.ManyToManyField('ProductImage', through='VariantImage')
    track_inventory = models.BooleanField(default=True)
    quantity = models.IntegerField(
        validators=[MinValueValidator(0)], default=Decimal(1))
    quantity_allocated = models.IntegerField(
        validators=[MinValueValidator(0)], default=Decimal(0))
    cost_price = models.DecimalField(max_digits=10, decimal_places=2,default=0.0)
    selling_price=models.DecimalField(max_digits=10,decimal_places=2,default=0.0)
    weight = models.DecimalField(max_digits=10,decimal_places=2,default=0.0)

    class Meta:
        app_label = 'product'

    def __str__(self):
        return self.name or self.sku

    @property
    def quantity_available(self):
        return max(self.quantity - self.quantity_allocated, 0)

    def check_quantity(self, quantity):
        """Check if there is at least the given quantity in stock
        if stock handling is enabled.
        """
        if self.track_inventory and quantity > self.quantity_available:
             raise InsufficientStock(self)
    # def get_weight(self):
    #     return (
    #         self.weight or self.product.weight or
    #         self.product.product_type.weight)

    def get_absolute_url(self):
        return reverse('product_productvariant_detail', args=(self.pk,))


    def get_update_url(self):
        return reverse('product_productvariant_update', args=(self.pk,))

    def is_in_stock(self):
        return self.quantity_available > 0

    def display_product(self, translated=False):
        if translated:
            product = self.product.translated
            variant_display = str(self.translated)
        else:
            variant_display = str(self)
            product = self.product
        product_display = (
            '%s (%s)' % (product, variant_display)
            if variant_display else str(product))
        return smart_text(product_display)

    def get_first_image(self):
        images = list(self.images.all())
        if images:
            return images[0].image
        return self.product.get_first_image()
    def get_ajax_label(self):
        return '%s, %s' % (
            self.sku, self.display_product())


class Attribute(models.Model):

    name = models.CharField(max_length=50)
    slug = AutoSlugField(populate_from='name', blank=True)

    class Meta:
        ordering = ('slug', )

    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse('product_attribute_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('product_attribute_update', args=(self.slug,))

    def get_formfield_name(self):
        return slugify('attribute-%s' % self.slug, allow_unicode=True)

    def has_values(self):
        return self.values.exists()

class AttributeValue(models.Model):
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100, default='')
    slug = AutoSlugField(populate_from='name', blank=True)
    attribute = models.ForeignKey(
        Attribute, related_name='values', on_delete=models.CASCADE)

    class Meta:
        ordering = ('-id',)
        unique_together = ('name', 'attribute')

    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse('product_attributevalue_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('product_attributevalue_update', args=(self.slug,))

    def get_ordering_queryset(self):
        return self.attribute.values.all()


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name='images', on_delete=models.CASCADE)
    image = VersatileImageField(
        upload_to='product/', ppoi_field='ppoi', blank=False)
    ppoi = PPOIField('Image PPOI')
    alt = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ('-id', )
        app_label = 'product'
    def get_absolute_url(self):
        return reverse('product_productimage_detail', args=(self.pk,))


    def get_update_url(self):
        return reverse('product_productimage_update', args=(self.pk,))

    def get_ordering_queryset(self):
        return self.product.images.all()

class VariantImage(models.Model):
    variant = models.ForeignKey(
        'ProductVariant', related_name='variant_images',
        on_delete=models.CASCADE)
    image = models.ForeignKey(
        ProductImage, related_name='variant_images', on_delete=models.CASCADE)
    def get_absolute_url(self):
        return reverse('product_variantimage_detail', args=(self.pk,))


    def get_update_url(self):
        return reverse('product_variantimage_update', args=(self.pk,))

class Stock(models.Model):
    variant=models.OneToOneField(ProductVariant,on_delete=models.CASCADE)
    slug = AutoSlugField(populate_from='variant', blank=True)
    Qih=models.IntegerField()
    reorderat=models.IntegerField(default=1)
    created=models.DateTimeField(auto_now_add=True)
    updated_on=models.DateTimeField(auto_now=True)
    totalwt=models.DecimalField(max_digits=10,decimal_places=3,default=0.0)

    class Meta:
        ordering=('-created',)

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('product_stock_detail', args=(self.slug,))

    def get_update_url(self):
        return reverse('product_stock_update', args=(self.slug,))

    def get_current_qih(self):
        return self.stocktransaction_set.all().aggregate(total=Sum('quantity'))

    def get_current_qih_weight(self):
        return self.stocktransaction_set.all().aggregate(total=Sum('weight'))


class StockTransaction(models.Model):

    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)
    type_choices=(("In","In"),("Out","Out"))
    type=models.CharField(max_length=3,choices=type_choices)
    quantity=models.IntegerField()
    weight=models.DecimalField(max_digits=10,decimal_places=3)
    description=models.TextField()

    #relational Fields
    stock=models.ForeignKey(Stock,on_delete=models.CASCADE)
    content_type=models.ForeignKey(ContentType,on_delete=models.CASCADE,null=True,blank=True)
    object_id=models.PositiveIntegerField(null=True,blank=True)
    content_object=GenericForeignKey('content_type','object_id')
    class Meta:
        ordering=('-created',)

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        return reverse('product_stocktransaction_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('product_stocktransaction_update', args=(self.pk,))

    def save(self,*args,**kwargs):
        if self.type =="Out":
            if self.quantity>0:
                self.quantity= -self.quantity
            self.weight= -self.weight
        super(StockTransaction, self).save(*args, **kwargs)
