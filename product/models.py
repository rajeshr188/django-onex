from decimal import Decimal
from django.forms.fields import DecimalField
from django_extensions.db.fields import AutoSlugField
from django.contrib.postgres.fields import HStoreField
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q,Sum
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.encoding import smart_text
from django.utils.text import slugify
# from django_measurement.models import MeasurementField
# from measurement.measures import Weight
from mptt.managers import TreeManager
from mptt.models import MPTTModel,TreeForeignKey
from versatileimagefield.fields import PPOIField, VersatileImageField
from .weight import WeightUnits, zero_weight
from django.contrib.contenttypes.fields import GenericForeignKey,GenericRelation
from django.contrib.contenttypes.models import ContentType
from .managers import StockManager
from utils.friendlyid import encode
class Category(MPTTModel):
    # gold ,silver ,other
    name = models.CharField(max_length=128,unique=True)
    slug = AutoSlugField(populate_from='name', blank=True)
    description = models.TextField(blank=True)
    parent = TreeForeignKey(
        'self', null=True, blank=True, related_name='children',
        on_delete=models.CASCADE)
    background_image = VersatileImageField(
        upload_to='category-backgrounds', blank=True, null=True)

    class MPPTMeta:
        order_insertion_by = ['name']

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
        app_label = 'product'
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
    name = models.CharField(max_length=128,unique = True)
    description = models.TextField()
    category = models.ForeignKey(
        Category, related_name='products', on_delete=models.CASCADE)
    attributes = HStoreField(default=dict, blank=True)

    class Meta:
        app_label = 'product'
        ordering=('name',)

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

    # def get_slug(self):
    #     return slugify(smart_text(unidecode(self.name)))

    def is_in_stock(self):
        return any(variant.is_in_stock() for variant in self)

    def get_first_image(self):
        images = list(self.images.all())
        return images[0].image if images else None

class ProductVariant(models.Model):
    sku = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255,unique = True)
    product = models.ForeignKey(
        Product, related_name='variants', on_delete=models.CASCADE)

    product_code = models.CharField(max_length=32,unique = True)
    attributes = HStoreField(default=dict, blank=True)
    images = models.ManyToManyField('ProductImage', through='VariantImage')
    # below fields not required?
    track_inventory = models.BooleanField('Tracked',default=True)
    quantity = models.IntegerField(
        validators=[MinValueValidator(0)], default=Decimal(1))
    quantity_allocated = models.IntegerField(
        validators=[MinValueValidator(0)], default=Decimal(0))
    

    class Meta:
        app_label = 'product'

    def __str__(self):
        return f"{self.name} {self.product_code}"

    @property
    def quantity_available(self):
        return max(self.quantity - self.quantity_allocated, 0)

    # def check_quantity(self, quantity):
    #     """Check if there is at least the given quantity in stock
    #     if stock handling is enabled.
    #     """
    #     if self.track_inventory and quantity > self.quantity_available:
    #          raise InsufficientStock(self)
    # def get_weight(self):
    #     return (
    #         self.weight or self.product.weight or
    #         self.product.product_type.weight)

    def get_bal(self):
        
        st = StockTransaction.objects.filter(stock__variant_id = self.id)
        ins = st.filter(activity_type__in=['P','SR','AR']).aggregate(
            wt = Sum('weight'),qty=Sum('quantity'))
        out = st.filter(activity_type__in=['S', 'PR', 'A']).aggregate(
            wt=Sum('weight'), qty=Sum('quantity'))
        total = {'wt':ins['wt']-out['wt'],'qty':ins['qty']-out['qty']}
        return total
                
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

# class ProductPrice(models.Model):
#     product = models.ForeignKey('ProductVariant',on_delete = models.CASCADE)
#     price = models.IntegerField()
#     def __str__(self):
#         return f"{self.price}"

# class CostPrice(models.Model):
#     productprice = models.ForeignKey('ProductPrice',on_delete = models.CASCADE)
#     contact = models.ForeignKey('contact.Customer',on_delete = models.CASCADE)

#     def __str__(self):
#         return f"{self.price}"

class Attribute(models.Model):

    name = models.CharField(max_length=50)
    slug = AutoSlugField(populate_from='name', blank=True)

    class Meta:
        ordering = ('id', )

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
    created = models.DateTimeField(auto_now_add = True)
    updated_on = models.DateTimeField(auto_now=True)
    reorderat = models.IntegerField(default=1)
    barcode = models.CharField(max_length=6, null = True,
                        blank=True, unique=True,editable = False)
    huid = models.CharField(max_length=6,null=True,blank=True,unique = True)
    variant = models.ForeignKey(ProductVariant, 
                                    on_delete=models.CASCADE,
                                    # related_name = 'stocks'
                                    )

    # following atrributes are not in dnf  i.e duplkicates of variant
    melting = models.DecimalField(max_digits =10,decimal_places=3, default =100)
    cost = models.DecimalField(max_digits = 10,decimal_places = 3,default = 100)
    touch = models.DecimalField(max_digits =10,decimal_places =3,default = 0)
    wastage = models.DecimalField(max_digits =10 ,decimal_places =3,default = 0) 
    tracking_type = models.CharField(choices = (
                                            ('Lot','Lot'),('Unique','Unique')),
                                            null = True,max_length=10,
                                            default = 'Lot') 
    
    status = models.CharField(max_length=10,choices = (
                                    ('Empty','Empty'),
                                    ('Available','Available'),('Sold','Sold'),
                                    ('Approval','Approval'),('Return','Return'),
                                    ('Merged','Merged'),
                                    ),
                                    default = 'Empty')
    objects = StockManager()
    class Meta:
        ordering=('-created',)
        
    def __str__(self):
        cb = self.current_balance()
        return f"{self.variant} {self.barcode} {cb['wt']} {cb['qty']}"

    def get_absolute_url(self):
        return reverse('product_stock_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('product_stock_update', args=(self.pk,))
    
    def get_pure_by_melting(self):
        bal = self.current_balance()
        return bal['wt']*self.melting

    def get_pure_by_cost(self):
        bal = self.current_balance()
        return bal['wt']*self.cost

    def audit(self):
        # get last audit cb,totalin,total out and then append following
        try:
            last_statement = self.stockstatement_set.latest()
        except StockStatement.DoesNotExist:
            last_statement = None
        if last_statement is not None:
            ls_wt = last_statement.Closing_wt
            ls_qty = last_statement.Closing_qty
        else:
            ls_wt = 0
            ls_qty = 0

        stock_in = self.stock_in_txns(last_statement)
        stock_out = self.stock_out_txns(last_statement)
        cb_wt =  ls_wt + (stock_in['wt'] - stock_out['wt'])
        cb_qty = ls_qty + (stock_in['qty'] - stock_out['qty'])

        return StockStatement.objects.create(stock = self,
                    Closing_wt = cb_wt,
                    Closing_qty = cb_qty,
                    total_wt_in = stock_in['wt'],
                    total_qty_in = stock_in['qty'],
                    total_wt_out = stock_out['wt'],
                    total_qty_out = stock_out['qty'])

    def stock_in_txns(self,ls):
        # filter since last audit
        st = self.stocktransaction_set.all()
        if ls :
            st.filter(created__gte = ls.created)
        st = self.stocktransaction_set.filter(
            activity_type__in=['P', 'SR', 'AR', 'AD'])

        return st.aggregate(
            qty=Coalesce(
                Sum('quantity', output_field=models.IntegerField()), 0),
            wt=Coalesce(
                Sum('weight', output_field=models.DecimalField()), Decimal(0.0))
        )
        
    def stock_out_txns(self,ls):
        # filter since last audit
        
        st = self.stocktransaction_set.all()
        if ls:
            st = st.filter(created__gte = ls.created)
        st = st.filter(
            activity_type__in=['PR', 'S', 'A', 'RM'])
        
        return st.aggregate(
                            qty=Coalesce(
                                Sum('quantity', output_field=models.IntegerField()), 0),
                            wt=Coalesce(Sum('weight',output_field = models.DecimalField()), Decimal(0.0))
                        )

    def current_balance(self):
        # compute cb from last audit and append following
        
        bal = {}
        try:
            ls = self.stockstatement_set.latest()  
            Closing_wt = ls.Closing_wt
            Closing_qty = ls.Closing_qty 
        except StockStatement.DoesNotExist:
            ls = None
            Closing_wt =0
            Closing_qty =0
        in_txns = self.stock_in_txns(ls)
        out_txns = self.stock_out_txns(ls)
        bal['wt'] = Closing_wt + (in_txns['wt'] - out_txns['wt'])
        bal['qty'] = Closing_qty + (in_txns['qty'] - out_txns['qty'])
        return bal

    def get_age(self):
        pass
        # if self.tracking_type == 'Lot':
        #     get average of purchase date from today and average of sale dates from today then sub both
        #     return 0
        # else:
            # check if sold then timedelta between created and last sales transaction
            # else timedelta between today and date created

    def add(self,Wih,Qih,cto,at):
        StockTransaction.objects.create(
                        stock = self,
                        weight = Wih,
                        quantity = Qih,
                        content_object = cto,
                        activity_type=at
                )
        self.update_status()

    def remove(self,weight,quantity,cto,at):
        cb = self.current_balance()
        if (cb['wt'] >= weight and cb['qty'] >= quantity):
            StockTransaction.objects.create(
                        stock = self,
                        weight = weight,
                        quantity = quantity,
                        content_object = cto,
                        activity_type=at
                )
            self.update_status()
            
        else:
            print("error here")
            raise Exception(f" qty/wt mismatch .hence exception")

    def split(self,weight):
        # split from stock:tracking_type::lot to unique
        cb = self.current_balance()
        if self.tracking_type == "Lot" and cb['wt'] >= weight and cb['qty'] >1:
            print('splitting')
            
            uniq_stock = Stock.objects.create(variant = self.variant,
                    tracking_type = 'Unique')
            uniq_stock.barcode='je'+ str(uniq_stock.id)
            
            uniq_stock.melting = self.melting
            uniq_stock.cost = self.cost
            uniq_stock.touch = self.touch
            uniq_stock.wastage = self.wastage
            uniq_stock.add(weight,1,
                            None,'AD')
            self.remove(weight,1,None,at = 'RM')
        else:
            print('unique nodes cant be split.hint:merge to lot and then split')

    def merge(self):
        # merge stock:tracking_type:unique to lot
        if self.tracking_type == "Unique":
            print('merging')
            lot = Stock.objects.get(variant = self.variant,tracking_type = "Lot")
            cb=self.current_balance()
            lot.add(cb['wt'],cb['qty'],None,'AD')
            self.remove(cb['wt'],cb['qty'],None,at = "RM")      
        else:
            print('lot cant be merged further')
    
    def transfer():
        pass

    def update_status(self):
        cb = self.current_balance()
        if cb['wt'] <= 0.0 or cb['qty'] <=0:
            self.status = "Empty"
        else:
            self.status = "Available"
        self.save()

    def save(self,*args,**kwargs):
        super(Stock, self).save(*args, **kwargs)
        if not self.barcode:
            self.barcode = encode(self.pk)
            super(Stock, self).save(*args, **kwargs)


class StockTransaction(models.Model):

    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)
    quantity=models.IntegerField(default=0)
    weight=models.DecimalField(max_digits=10,decimal_places=3,default=0)
    description=models.TextField()

    PURCHASE = 'P'
    PURCHASERETURN = 'PR'
    SALES = 'S'
    SALESRETURN = 'SR'
    APPROVAL = 'A'
    APPROVALRETURN = 'AR'
    REMOVE = 'RM'
    ADD = 'AD'
    ACTIVITY_TYPES = (
        (PURCHASE, 'Purchase'),
        (PURCHASERETURN, 'Purchase Return'),
        (SALES, 'Sales'),
        (SALESRETURN, 'Sales Return'),
        (APPROVAL, 'Approval'),
        (APPROVALRETURN, 'Approval Return'),
        (REMOVE,'Remove'),
        (ADD,'Add'),
    )

    # user = models.ForeignKey(User)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES,default = "PURCHASE")
    #relational Fields
    stock = models.ForeignKey(Stock,on_delete=models.CASCADE)

    # is generic foreignkey required here? 
    content_type=models.ForeignKey(ContentType,on_delete=models.CASCADE,
                                                        null=True,blank=True)
    object_id=models.PositiveIntegerField(null=True,blank=True)
    content_object=GenericForeignKey('content_type','object_id')

    class Meta:
        ordering=('-created',)
        get_latest_by = ['created']

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        return reverse('product_stocktransaction_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('product_stocktransaction_update', args=(self.pk,))

class StockStatement(models.Model):
    stock = models.ForeignKey(Stock, on_delete = models.CASCADE)
    created = models.DateTimeField(auto_now = True)
    Closing_wt = models.DecimalField(max_digits = 14, decimal_places = 3)
    Closing_qty = models.IntegerField()
    total_wt_in = models.DecimalField(max_digits = 14, decimal_places = 3)
    total_wt_out = models.DecimalField(max_digits = 14, decimal_places = 3)
    total_qty_in = models.IntegerField()
    total_qty_out = models.IntegerField()

    class Meta:
        ordering = ('created',)
        get_latest_by = ['created']

    def __str__(self):
        return f"{self.stock} - qty:{self.Closing_qty} wt:{self.Closing_wt}"
