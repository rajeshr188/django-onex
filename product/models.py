from dea.models import Journal
from decimal import Decimal
from product.attributes import get_product_attributes_data
from django_extensions.db.fields import AutoSlugField
from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.db.models import Sum,F,Q,ExpressionWrapper
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
from .managers import StockManager
from utils.friendlyid import encode

class Category(MPTTModel):
    # gold ,silver ,other
    name = models.CharField(max_length=128,unique=True)
    slug = AutoSlugField(populate_from='name', blank=True)
    description = models.TextField(blank=True)
    parent = TreeForeignKey('self', null=True, blank=True,
            related_name='children',on_delete=models.CASCADE)
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
        ordering=('id',)

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
    product_type = models.ForeignKey(ProductType, 
                related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=128,unique = True)
    description = models.TextField()
    category = models.ForeignKey(Category, 
                related_name='products', on_delete=models.CASCADE)
    attributes = HStoreField(default=dict, blank=True)
    jattributes = models.JSONField(default = dict,blank = True,null = True)

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

    def is_in_stock(self):
        return any(variant.is_in_stock() for variant in self)

    def get_first_image(self):
        images = list(self.images.all())
        return images[0].image if images else None

    def get_attributes(self):
        return get_product_attributes_data(self)

class ProductVariant(models.Model):
    sku = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255,unique = True)
    product = models.ForeignKey(Product, 
                related_name='variants', on_delete=models.CASCADE)
    product_code = models.CharField(max_length=32,unique = True)
    attributes = HStoreField(default=dict, blank=True)
    jattributes = models.JSONField(default = dict)
    images = models.ManyToManyField('ProductImage', through='VariantImage')
 
    class Meta:
        app_label = 'product'

    def __str__(self):
        return f"{self.name} {self.product_code}"

    def get_attributes(self):
        return get_product_attributes_data(self.product)

    def get_bal(self):
        st = StockBalance.objects.get(stock__variant_id = self.id)
        total = {
            'wt':st.Closing_wt + st.in_wt -st.out_wt,
            'qty':st.Closing_qty + st.in_qty - st.out_qty
        }
        # st = StockTransaction.objects.filter(stock__variant_id = self.id)
        # ins = st.filter(movement_type_id__in=['P','SR','AR'])
        # i={}
        # o={}
        # if ins.exists():
        #     i = ins.aggregate(
        #     wt = Sum('weight'),qty=Sum('quantity'))
           
        # else:
        #     i['wt']=0
        #     i['qty']=0
        # out = st.filter(movement_type__id__in=['S', 'PR', 'A'])
        # if out.exists():
        #     o = out.aggregate(
        #     wt=Sum('weight'), qty=Sum('quantity'))
        # else:
        #     o['wt']=0
        #     o['qty']=0

        # total = {'wt':i['wt']-o['wt'],'qty':i['qty']-o['qty']}
        return total
                
    def get_absolute_url(self):
        return reverse('product_productvariant_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('product_productvariant_update', args=(self.pk,))

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
    product = models.ForeignKey(Product, 
            related_name='images', on_delete=models.CASCADE)
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

class StockManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related()
    def with_bal(self):
        return self.annotate(
            qty = F('stockbalance__Closing_qty') + F('stockbalance__in_qty') - F('stockbalance__out_qty'),
            wt = F('stockbalance__Closing_wt') + F('stockbalance__in_wt') - F('stockbalance__out_wt')
        )

class Stock(models.Model):
    created = models.DateTimeField(auto_now_add = True)
    updated_on = models.DateTimeField(auto_now=True)
    reorderat = models.IntegerField(default=1)
    barcode = models.CharField(max_length=6, null = True,
                blank=True, unique=True,editable = False)
    huid = models.CharField(max_length=6,null=True,blank=True,unique = True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE,
                                    # related_name = 'stocks'
            )

    # following atrributes are not in dnf  i.e duplkicates of variant
    melting = models.DecimalField(max_digits =10,decimal_places=3, default =100)
    cost = models.DecimalField(max_digits = 10,decimal_places = 3,default = 100)
    touch = models.DecimalField(max_digits =10,decimal_places =3,default = 0)
    wastage = models.DecimalField(max_digits =10 ,decimal_places =3,default = 0) 
    tracking_type = models.CharField(choices = (('Lot','Lot'),
                    ('Unique','Unique')),verbose_name='track_by',
                    null = True,max_length=10,default = 'Lot') 
    
    status = models.CharField(max_length=10,choices = (
                ('Empty','Empty'),('Available','Available'),('Sold','Sold'),
                ('Approval','Approval'),('Return','Return'),('Merged','Merged'),
                ),default = 'Empty')
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
        
        if self.tracking_type == 'Lot':
            sbs = self.stockbatch_set.all()
            for i in sbs:
                print(f"auditing {i}")
                i.audit()
        try:
            last_statement = self.stockstatement_set.filter(sstype = 'Stock').latest()
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
                    sstype='Stock',
                    total_wt_in = stock_in['wt'],
                    total_qty_in = stock_in['qty'],
                    total_wt_out = stock_out['wt'],
                    total_qty_out = stock_out['qty'])

    def stock_in_txns(self,ls):
        # filter since last audit
        st = self.stocktransaction_set.all()
        if ls :
            st = st.filter(created__gte = ls.created)
        st = st.filter(
            movement_type__id__in=['P', 'SR', 'AR', 'AD'])

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
            movement_type__id__in=['PR', 'S', 'A', 'RM'])
        
        return st.aggregate(
                    qty=Coalesce(Sum('quantity', output_field=models.IntegerField()), 0),
                    wt=Coalesce(Sum('weight',output_field = models.DecimalField()), Decimal(0.0)))

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

    def add(self,weight,quantity,journal,activity_type,stockbatch= None):
        if self.tracking_type =='Unique' or stockbatch:
             StockTransaction.objects.create(journal = journal,
                stock = self,stock_batch = stockbatch,weight = weight,quantity = quantity,
                movement_type_id=activity_type)
        else:
            #fillup given quantity to latest empty batches
            empty_stbt = self.stockbatchbalance_set.order_by('-stock_batch__created').annotate(
                qty = F('Closing_qty') + F('in_qty') - F('out_qty'),
                wt = F('Closing_wt') + F('in_wt') - F('out_wt')
            ).filter(
                Q(qty = 0) & Q(wt = 0)
                )
            w = weight
            q = quantity
            for i in empty_stbt:
                qty = i.get_qty_bal()
                wt = i.get_wt_bal()
                
                if w ==0 and q == 0:break
                elif qty <= q and wt <= w:
                    StockTransaction.objects.create(
                        journal = journal,
                        stock = self,
                        stock_batch = i.stock_batch,
                        weight = w,quantity = q,
                        movement_type_id = activity_type
                    )
                    break
                else:
                    StockTransaction.objects.create(
                        journal = journal,
                        stock = self,
                        stock_batch = i.stock_batch,
                        weight = wt,quantity = qty,
                        movement_type_id = activity_type
                    )
                    w = w - wt
                    q = q-qty

        self.update_status()
    
    def remove(self,weight,quantity,journal,activity_type):
        if self.tracking_type == 'Unique':
            StockTransaction.objects.create(
                journal = journal,
                stock=self,
                weight=weight,quantity=quantity,
                activity_type=activity_type)
            self.update_status()
        else:
            # get batches in lifo 
            stbs = self.stockbatchbalance_set.order_by('stock_batch__created').annotate(
                qty = F('Closing_qty') + F('in_qty') - F('out_qty'),
                wt = F('Closing_wt') + F('in_wt') - F('out_wt')
            ).filter(
                Q(qty__gt = 0)& Q(wt__gt = 0)
            )
            print(f"stbs : {stbs}")
            wt = weight
            qty  = quantity
            print(f"weight:{weight} qty:{quantity}")
            for i in stbs:
                print(f"i of stbs: {i}")
                q = i.get_qty_bal()
                w = Decimal(i.get_wt_bal())
                print(f"w:{w} q:{q}")
                if wt <=0.0 and qty <=0:break
                else:
                    if q >= qty and w >= wt:
                        print("creating stock transaction with wt:{wt} qty:{qty}")
                        StockTransaction.objects.create(
                            journal = journal,
                            stock=self,
                            stock_batch = i.stock_batch,
                            weight=wt,quantity=qty,
                            movement_type_id =activity_type
                        )
                        break
                    else:
                        print("creating stock transaction with wt:{w} qty:{q}")

                        StockTransaction.objects.create(
                            journal=journal,
                            stock=self,
                            stock_batch=i.stock_batch,
                            weight=w, quantity=q,
                            movement_type_id =activity_type
                        )
                        wt = wt - w
                        qty = qty - q

    def create_batch(self,weight,quantity):
        return StockBatch.objects.create(stock = self,weight=weight,quantity=quantity)

    def split(self,weight):
        # split from stock:tracking_type::lot to unique
        cb = self.current_balance()
        if self.tracking_type == "Lot" and cb['wt'] >= weight and cb['qty'] >1:
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
            self.save()

class StockBatch(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    quantity = models.IntegerField(default =0)
    weight = models.DecimalField(max_digits=10,decimal_places=3)

    stock = models.ForeignKey(Stock,on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}"

    def add(self,weight,quantity,journal,activity_type):
        StockTransaction.objects.create(journal=journal,
                                        stock = self.stock,
                                        stock_batch=self, weight=weight, quantity=quantity,
                                        movement_type_id=activity_type)
        self.stock.update_status()

    def remove(self, weight, quantity, journal, activity_type):
        StockTransaction.objects.create(
            journal=journal,
            stock=self.stock,
            stock_batch = self,
            weight=weight, quantity=quantity,
            movement_type_id=activity_type)
        self.stock.update_status()

    def audit(self):
        try:
            last_statement = self.stockstatement_set.filter(
                sstype='Stockbatch').latest()
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
        cb_wt = ls_wt + (stock_in['wt'] - stock_out['wt'])
        cb_qty = ls_qty + (stock_in['qty'] - stock_out['qty'])

        return StockStatement.objects.create(stock =self.stock,
                                             stock_batch = self,
                                             Closing_wt=cb_wt,
                                             Closing_qty=cb_qty,
                                             sstype='Stockbatch',
                                             total_wt_in=stock_in['wt'] if stock_in['wt'] else 0.0,
                                             total_qty_in=stock_in['qty']if stock_in['qty'] else 0,
                                             total_wt_out=stock_out['wt']if stock_out['wt'] else 0.0,
                                             total_qty_out=stock_out['qty']if stock_out['qty'] else 0)

    def stock_in_txns(self, ls):
        # filter since last audit
        st = self.stocktransaction_set.all()
        if ls:
            st = st.filter(created__gte=ls.created)
        st = st.filter(
            movement_type__id__in=['P', 'SR', 'AR', 'AD'])

        return st.aggregate(
            qty=Coalesce(
                Sum('quantity', output_field=models.IntegerField()), 0),
            wt=Coalesce(
                Sum('weight', output_field=models.DecimalField()), Decimal(0.0))
        )

    def stock_out_txns(self, ls):
        # filter since last audit
        st = self.stocktransaction_set.all()
        if ls:
            st = st.filter(created__gte=ls.created)
        st = st.filter(
            movement_type__id__in=['PR', 'S', 'A', 'RM'])

        return st.aggregate(
            qty=Coalesce(
                Sum('quantity', output_field=models.IntegerField()), 0),
            wt=Coalesce(Sum('weight', output_field=models.DecimalField()), Decimal(0.0)))

    def current_balance(self):
        # compute cb from last audit and append following
        bal = {}
        try:
            ls = self.stockstatement_set.filter(sstype='Stockbatch').latest()
            Closing_wt = ls.Closing_wt
            Closing_qty = ls.Closing_qty
        except StockStatement.DoesNotExist:
            ls = None
            Closing_wt = 0
            Closing_qty = 0
        in_txns = self.stock_in_txns(ls)
        out_txns = self.stock_out_txns(ls)
        bal['wt'] = Closing_wt + (in_txns['wt'] - out_txns['wt'])
        bal['qty'] = Closing_qty + (in_txns['qty'] - out_txns['qty'])
        return bal

class Movement(models.Model):
    id = models.CharField(max_length = 3,primary_key=True)
    name = models.CharField(max_length = 30)
    direction = models.CharField(max_length = 1,default = '+')

class StockTransaction(models.Model):

    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)
    quantity=models.IntegerField(default=0)
    weight=models.DecimalField(max_digits=10,decimal_places=3,default=0)
    description=models.TextField()

    # user = models.ForeignKey(CustomUser)
    movement_type = models.ForeignKey(Movement,on_delete = models.CASCADE)

    #relational Fields
    stock = models.ForeignKey(Stock,on_delete=models.CASCADE)
    stock_batch = models.ForeignKey(StockBatch,null = True,blank = True,
                                    on_delete=models.CASCADE)
    
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, 
                related_name='stxns')

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
    ss_method = (
        ("Auto","Auto"),
        ("Physical","Physical"),
    )
    method = models.CharField(max_length=20,choices=ss_method,default="Auto")
    ss_type = (
        ("Stock","Stock"),
        ("Stockbatch",'Stockbatch'),
    )
    sstype = models.CharField(max_length=20,choices = ss_type,default = 'Stock')
    stock = models.ForeignKey(Stock, on_delete = models.CASCADE)
    stock_batch = models.ForeignKey(StockBatch,on_delete = models.CASCADE,
                            null = True,blank = True)
    created = models.DateTimeField(auto_now = True)
    Closing_wt = models.DecimalField(max_digits = 14, decimal_places = 3)
    Closing_qty = models.IntegerField()
    total_wt_in = models.DecimalField(max_digits = 14, decimal_places = 3,
                    default =0.0)
    total_wt_out = models.DecimalField(max_digits = 14, decimal_places = 3,default=0.0)
    total_qty_in = models.IntegerField(default =0.0)
    total_qty_out = models.IntegerField(default=0.0)

    class Meta:
        ordering = ('created',)
        get_latest_by = ['created']

    def __str__(self):
        return f"{self.stock} - qty:{self.Closing_qty} wt:{self.Closing_wt}"

class StockBalance(models.Model):
    stock = models.OneToOneField(Stock,on_delete=models.DO_NOTHING,primary_key=True)
    Closing_wt = models.DecimalField(max_digits = 14, decimal_places = 3)
    Closing_qty = models.IntegerField()
    in_wt = models.DecimalField(max_digits=14, decimal_places=3)
    in_qty = models.IntegerField()
    out_wt = models.DecimalField(max_digits=14, decimal_places=3)
    out_qty = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'stock_balance'

    def get_qty_bal(self):
        return self.Closing_qty + self.in_qty - self.out_qty

    def get_wt_bal(self):
        return self.Closing_wt + self.in_wt - self.out_wt
    
class StockBatchBalance(models.Model):
    stock = models.ForeignKey(Stock,on_delete = models.DO_NOTHING)
    stock_batch = models.OneToOneField(StockBatch, on_delete=models.DO_NOTHING,primary_key=True)
    Closing_wt = models.DecimalField(max_digits = 14, decimal_places = 3)
    Closing_qty = models.IntegerField()
    in_wt = models.DecimalField(max_digits=14, decimal_places=3,default= 0.0)
    in_qty = models.IntegerField(default =0)
    out_wt = models.DecimalField(max_digits=14, decimal_places=3,default=0.0)
    out_qty = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table ='stockbatch_balance'

    def get_qty_bal(self):
        return self.Closing_qty + self.in_qty - self.out_qty 

    def get_wt_bal(self):
        return self.Closing_wt + self.in_wt  - self.out_wt 

