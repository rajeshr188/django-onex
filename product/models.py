from decimal import Decimal
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

    product_code = models.CharField(max_length=32,default='kas')
    attributes = HStoreField(default=dict, blank=True)
    images = models.ManyToManyField('ProductImage', through='VariantImage')
    track_inventory = models.BooleanField('Tracked',default=True)
    quantity = models.IntegerField(
        validators=[MinValueValidator(0)], default=Decimal(1))
    quantity_allocated = models.IntegerField(
        validators=[MinValueValidator(0)], default=Decimal(0))
    # add melting,wh_va,ret_va
    # weight = models.DecimalField(max_digits=10,decimal_places=2,default=0.0)
    # melting = models.DecimalField(max_digits=10,decimal_places=3,default = 0.0)
    # cost = models.DecimalField(max_digits=10, decimal_places=2,default=0.0)
    # touch = models.DecimalField(max_digits=10, decimal_places=2,default=0.0)
    # wastage = models.DecimalField(max_digits=10, decimal_places=2,default=0.0)
    # selling_price=models.DecimalField(max_digits=10,decimal_places=2,default=0.0)

    class Meta:
        app_label = 'product'

    def __str__(self):
        return f"{self.name} {self.product_code}"

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

    def get_weight(self):
        return Stock.objects.filter(variant = self).aggregate(t = Sum('weight'))

    def get_wih(self):
        return Stock.objects.filter(variant = self).aggregate(t = Sum('Wih'))

    def get_qty(self):
        return Stock.objects.filter(variant = self).aggregate(t = Sum('quantity'))

    def get_qih(self):
        return Stock.objects.filter(variant = self).aggregate(t = Sum('Qih'))

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

class Stree(MPTTModel):
    # each stree is a node or shadow of product variant in lot or unique
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=100,blank = True,null = True,default = '')
    parent = TreeForeignKey('self',null = True,blank = True,
                            related_name = 'children',
                            on_delete = models.CASCADE)
    # duplicates of weight cost touch wastage from product variant
    weight = models.DecimalField(decimal_places=3,max_digits=10,null = True,default=0)
    cost = models.DecimalField(decimal_places=3,max_digits=10,null = True,default=0)
    touch = models.DecimalField(decimal_places=3,max_digits=10,default=0)
    wastage = models.DecimalField(decimal_places=2,max_digits=10,null=True,default=0)

    tracking_type = models.CharField(choices = (
                                            ('Lot','Lot'),('Unique','Unique')),
                                            null = True,max_length=10,
                                            default = 'Lot')
    barcode = models.CharField(max_length=100,null=True,default = '')
    quantity = models.IntegerField(default=0,)
    status = models.CharField(max_length=10,choices = (
                                    ('Empty','Empty'),
                                    ('Available','Available'),('Sold','Sold'),
                                    ('Approval','Approval'),('Return','Return')
                                    ),
                                    default = 'Empty')
    productvariant = models.ForeignKey('ProductVariant',on_delete = models.CASCADE,null = True)

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return f"{self.get_root().name}:{self.productvariant} {self.barcode} wt:{self.weight} qty:{self.quantity}"

    def get_absolute_url(self):
        return reverse('product_stree_list')

    def get_update_url(self):
        return reverse('product_stree_update', args=(self.pk,))

    def balance(self):
        balances = [node.weight for node in self.get_descendants(include_self=True)]
        return sum(balances)

    def qty(self):
        qt = [node.quantity for node in self.get_descendants(include_self = True)]
        return sum(qt)

    def subtract(self,qty,wt):
        # assert(self.quantity >= qty),"quantity is higher than avaialble"
        # assert(self.weight >= wt),"weight more than available"
        if self.quantity >= qty and self.weight >= wt :
            self.quantity -=qty
            self.weight -= wt
            self.save()
            self.update_status()
        else:
            raise Exception(f" {self.quantity} > {qty} and {self.weight} > {wt} .hence exception")

    def add(self,qty,wt):
        self.quantity +=qty
        self.weight += wt
        self.save()
        self.update_status()

    def transfer(self,node,qty,wt):
        try:
            self.subtract(qty,wt)
        except Exception:
            print("transfer failed")
            raise Exception("transfer failed")
        else:
            node.add(qty,wt)
            node.save()

    def traverse_to(self,product,category='Gold'):
        print(f"self:{self} product:{product}")
        path_to_take = ['product_type','Purity','Weight','Gender','Design','Length','Initial','tracking_type']
        product_variant = product
        product_type = product_variant.product.product_type
        attr = {**product_variant.product.attributes,**product_variant.attributes}
        attr = {Attribute.objects.get(id = item[0]).name : AttributeValue.objects.get(id = item[1]).name for item in attr.items()}
        attr['product_type']= product_type.name
        attr = {i:attr[i]for i in path_to_take if i in attr}
        path = list(attr.values())
        path = [category]+path

        for p in path:
            self,status = Stree.objects.get_or_create(name=p,parent=self)
            # print(f"-->{self}")
        self.tracking_type = attr['tracking_type']
        self.save()
        return self

    def traverse_parellel_to(self,node,include_self = True):
        ancestors = [i.name for i in node.get_ancestors(include_self = include_self)]
        ancestors.pop(0)
        # print(f"ancestors : {ancestors}")
        for p in ancestors:
            self,status = Stree.objects.get_or_create(name=p,parent = self)
        return self

    def empty_stock(self):
        pass

    def split_node(self,weight):
        if self.weight < weight:
            return

        if self.get_siblings().count() == 0:
            sibling = Stree.objects.create(full_name=self.get_family()[1].name ,name = 'Unique',parent = self.parent,tracking_type='Unique')
            print(f"created sibling{sibling} of family{sibling.get_family()}")
            # sibling.insert_at(target = self,position='right')
        sibling = self.get_siblings()[0]

        newnode = Stree.objects.create(parent = sibling,weight=weight,tracking_type='Unique',quantity=1,status = 'Available')
        newnode.barcode = 'je'+str(newnode.id)
        family = newnode.get_family()
        newnode.full_name=family[2].name+family[3].name
        newnode.save()
        self.weight -= weight
        self.quantity -=1
        self.save()

    def merge_node(self):
        if self.tracking_type == 'Lot':
            return
        n = self.get_family()
        lot,status = Stree.objects.get_or_create(full_name=n[2].name+'Lot',name='Lot',parent = self.parent.parent,tracking_type='Lot')
        lot.weight += self.weight
        lot.quantity +=1
        lot.save()
        self.delete()

    def update_status(self):
        root = self.get_root()
        if root.name =='Stock':
            if self.weight == 0:
                self.status = 'Empty'
            else:
                self.status = 'Available'
        else :
            self.status = root.name
        self.save()

class Stock(models.Model):
    created = models.DateTimeField(auto_now_add = True)
    updated_on = models.DateTimeField(auto_now=True)

    melting = models.DecimalField(max_digits =10,decimal_places=3, default =100)
    cost = models.DecimalField(max_digits = 10,decimal_places = 3,default = 100)
    touch = models.DecimalField(max_digits =10,decimal_places =3,default = 0)
    wastage = models.DecimalField(max_digits =10 ,decimal_places =3,default = 0)
    weight = models.DecimalField(max_digits = 10, decimal_places = 3,
                                    default =0)
    quantity = models.IntegerField(default =0)
    Wih = models.DecimalField(max_digits=10,decimal_places=3,default=0)
    Qih = models.IntegerField(default=0)
    reorderat = models.IntegerField(default=1)
    tracking_type = models.CharField(choices = (
                                            ('Lot','Lot'),('Unique','Unique')),
                                            null = True,max_length=10,
                                            default = 'Lot')
    barcode = models.CharField(max_length=100,null=True,unique = True)
    status = models.CharField(max_length=10,choices = (
                                    ('Empty','Empty'),
                                    ('Available','Available'),('Sold','Sold'),
                                    ('Approval','Approval'),('Return','Return')
                                    ),
                                    default = 'Empty')
    variant=models.ForeignKey(ProductVariant,on_delete=models.CASCADE)

    class Meta:
        ordering=('-created',)

    def __str__(self):
        return f"{self.variant} {self.barcode} wt:{self.Wih} qty:{self.Qih}"

    def get_absolute_url(self):
        return reverse('product_stock_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('product_stock_update', args=(self.pk,))

    def get_computed_qih(self):
        # return self.stocktransaction_set.all().aggregate(total=Sum('quantity'))
        sum= self.stocktransaction_set.aggregate(
                                inw = Coalesce(Sum('quantity',filter = Q(type='In')),0),
                                out = Coalesce(Sum('quantity',filter = Q(type ='Out')),0),
                                )
        return (sum['inw']+sum['out'])

    def get_computed_wih(self):
        sum= self.stocktransaction_set.aggregate(
                                inw = Coalesce(Sum('weight',filter = Q(type='In')),0),
                                out = Coalesce(Sum('weight',filter = Q(type ='Out')),0),
                                )
        return (sum['inw']+sum['out'])

    def check_stock(self):
        return (self.Wih == self.get_computed_wih()) and (self.Qih == self.get_computed_qih())

    def get_age(self):
        pass
        # if self.tracking_type == 'Lot':
        #     get average of purchase date from today and average of sale dates from today then sub both
        #     return 0
        # else:
            # check if sold then timedelta between created and last sales transaction
            # else timedelta between today and date created
    def add(self,weight,qty,Wih,Qih,cto,at):
        if self.check_stock():
            self.weight += weight
            self.quantity += qty
            self.Qih += Qih
            self.Wih += Wih

            StockTransaction.objects.create(
                    stock = self,
                    type = "In",
                    weight = Wih,
                    quantity = Qih,
                    content_object = cto,
                    activity_type=at
            )
            self.update_status()
        else:
            raise Exception(f"Stock.check_stock() failed")

    def remove(self,weight,qty,Wih,Qih,cto,at):
        if self.check_stock():
            if (self.weight >= weight and self.quantity >= qty) and (self.Wih >= Wih and self.Qih >=Qih):
                self.weight -= weight
                self.quantity -= qty
                self.Qih -= Qih
                self.Wih -= Wih
                StockTransaction.objects.create(
                        stock = self,
                        type = "Out",
                        weight = Wih,
                        quantity = Qih,
                        content_object = cto,
                        activity_type=at
                )
                self.update_status()

            else:
                raise Exception(f" qty/wt mismatch .hence exception")
        else:
            raise Exception(f" Stock.check_Stock failed")

    def split(self,weight,qty,cto,at):
        if self.tracking_type == "Lot":
            print('splitting')
        else:
            print('unique nodes cant be split')

    def merge(self,weight,qty,cto,at):
        if self.tracking_type == "Unique":
            print('merging')
        else:
            print('lot cant be merged further')

    def update_status(self):
        if self.Wih <= 0.0 or self.Qih <=0:
            self.status = "Empty"
        else:
            self.status = "Available"
        self.save()


class StockTransaction(models.Model):

    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)
    type_choices=(("In","In"),("Out","Out"))
    type=models.CharField(max_length=3,choices=type_choices)
    quantity=models.IntegerField(default=0)
    weight=models.DecimalField(max_digits=10,decimal_places=3,default=0)
    description=models.TextField()
    PURCHASE = 'P'
    PURCHASERETURN = 'PR'
    SALES = 'S'
    SALESRETURN = 'SR'
    APPROVAL = 'A'
    APPROVALRETURN = 'AR'
    SPLIT = 'SP'
    MERGE = 'M'
    ACTIVITY_TYPES = (
        (PURCHASE, 'Purchase'),
        (PURCHASERETURN, 'Purchase Return'),
        (SALES, 'Sales'),
        (SALESRETURN, 'Sales Return'),
        (APPROVAL, 'Approval'),
        (APPROVALRETURN, 'Approval Return'),
        (SPLIT,'Split'),
        (MERGE,'Merge'),
    )

    # user = models.ForeignKey(User)
    activity_type = models.CharField(max_length=2, choices=ACTIVITY_TYPES)
    #relational Fields
    stock=models.ForeignKey(Stock,on_delete=models.CASCADE)
    content_type=models.ForeignKey(ContentType,on_delete=models.CASCADE,
                                                        null=True,blank=True)
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
