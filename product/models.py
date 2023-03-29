from decimal import Decimal

from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.urls import reverse
# from django.utils.encoding import smart_text
from django.utils.text import slugify
from django_extensions.db.fields import AutoSlugField
# from django_measurement.models import MeasurementField
# from measurement.measures import Weight
from mptt.managers import TreeManager
from mptt.models import MPTTModel, TreeForeignKey
from versatileimagefield.fields import PPOIField, VersatileImageField

from dea.models import Journal
from product.attributes import get_product_attributes_data
from utils.friendlyid import encode

from .managers import StockManager, StockLotManager
from .weight import WeightUnits, zero_weight


class Category(MPTTModel):
    # gold ,silver ,other
    name = models.CharField(max_length=128, unique=True)
    slug = AutoSlugField(populate_from="name", blank=True)
    description = models.TextField(blank=True)
    parent = TreeForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE
    )
    background_image = VersatileImageField(
        upload_to="category-backgrounds", blank=True, null=True
    )

    class MPPTMeta:
        order_insertion_by = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product_category_detail", args=(self.slug,))

    def get_update_url(self):
        return reverse("product_category_update", args=(self.slug,))


class ProductType(models.Model):
    # ring,bracelet,chain,necklace,harem,dollar,urupudi,coin,kalkas,moppu,mugti,kamal,tops,kassaset,jhapaka,mattal
    name = models.CharField(max_length=128)
    has_variants = models.BooleanField(default=True)
    product_attributes = models.ManyToManyField(
        "Attribute", related_name="product_types", blank=True
    )
    variant_attributes = models.ManyToManyField(
        "Attribute", related_name="product_variant_types", blank=True
    )

    class Meta:
        app_label = "product"
        ordering = ("name",)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product_producttype_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("product_producttype_update", args=(self.pk,))

    def __repr__(self):
        class_ = type(self)
        return "<%s.%s(pk=%r, name=%r)>" % (
            class_.__module__,
            class_.__name__,
            self.pk,
            self.name,
        )


class Product(models.Model):
    # tv ring,plate ring,dc chain,gc chain
    product_type = models.ForeignKey(
        ProductType, related_name="products", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField()
    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.CASCADE
    )
    attributes = HStoreField(default=dict, blank=True)
    jattributes = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        app_label = "product"
        ordering = ("name",)

    def __iter__(self):
        if not hasattr(self, "__variants"):
            setattr(self, "__variants", self.variants.all())
        return iter(getattr(self, "__variants"))

    def __repr__(self):
        class_ = type(self)
        return "<%s.%s(pk=%r, name=%r)>" % (
            class_.__module__,
            class_.__name__,
            self.pk,
            self.name,
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product_product_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("product_product_update", args=(self.pk,))

    def is_in_stock(self):
        return any(variant.is_in_stock() for variant in self)

    def get_first_image(self):
        images = list(self.images.all())
        return images[0].image if images else None

    def get_attributes(self):
        return get_product_attributes_data(self)


class ProductVariant(models.Model):
    sku = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255, unique=True)
    product = models.ForeignKey(
        Product, related_name="variants", on_delete=models.CASCADE
    )
    product_code = models.CharField(max_length=32, unique=True)
    attributes = HStoreField(default=dict, blank=True)
    jattributes = models.JSONField(default=dict)
    images = models.ManyToManyField("ProductImage", through="VariantImage")

    class Meta:
        app_label = "product"

    def __str__(self):
        return f"{self.name} {self.product_code}"

    def get_attributes(self):
        return get_product_attributes_data(self.product)

    def get_bal(self):
        st = StockTransaction.objects.filter(stock__variant_id=self.id)
        ins = st.filter(activity_type__in=["P", "SR", "AR"])
        i = {}
        o = {}
        if ins.exists():
            i = ins.aggregate(wt=Sum("weight"), qty=Sum("quantity"))

        else:
            i["wt"] = 0
            i["qty"] = 0
        out = st.filter(activity_type__in=["S", "PR", "A"])
        if out.exists():
            o = out.aggregate(wt=Sum("weight"), qty=Sum("quantity"))
        else:
            o["wt"] = 0
            o["qty"] = 0

        total = {"wt": i["wt"] - o["wt"], "qty": i["qty"] - o["qty"]}
        return total

    def get_absolute_url(self):
        return reverse("product_productvariant_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("product_productvariant_update", args=(self.pk,))

    def display_product(self, translated=False):
        if translated:
            product = self.product.translated
            variant_display = str(self.translated)
        else:
            variant_display = str(self)
            product = self.product
        product_display = (
            "%s (%s)" % (product, variant_display) if variant_display else str(product)
        )
        return product_display

    def get_first_image(self):
        images = list(self.images.all())
        if images:
            return images[0].image
        return self.product.get_first_image()

    def get_ajax_label(self):
        return "%s, %s" % (self.sku, self.display_product())


class Attribute(models.Model):
    name = models.CharField(max_length=50)
    slug = AutoSlugField(populate_from="name", blank=True)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product_attribute_detail", args=(self.slug,))

    def get_update_url(self):
        return reverse("product_attribute_update", args=(self.slug,))

    def get_formfield_name(self):
        return slugify("attribute-%s" % self.slug, allow_unicode=True)

    def has_values(self):
        return self.values.exists()


class AttributeValue(models.Model):
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100, default="")
    slug = AutoSlugField(populate_from="name", blank=True)
    attribute = models.ForeignKey(
        Attribute, related_name="values", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ("-id",)
        unique_together = ("name", "attribute")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product_attributevalue_detail", args=(self.slug,))

    def get_update_url(self):
        return reverse("product_attributevalue_update", args=(self.slug,))

    def get_ordering_queryset(self):
        return self.attribute.values.all()


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = VersatileImageField(
        upload_to="product/", ppoi_field="ppoi", blank=False)
    ppoi = PPOIField("Image PPOI")
    alt = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ("-id",)
        app_label = "product"

    def get_absolute_url(self):
        return reverse("product_productimage_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("product_productimage_update", args=(self.pk,))

    def get_ordering_queryset(self):
        return self.product.images.all()


class VariantImage(models.Model):
    variant = models.ForeignKey(
        "ProductVariant", related_name="variant_images", on_delete=models.CASCADE
    )
    image = models.ForeignKey(
        ProductImage, related_name="variant_images", on_delete=models.CASCADE
    )

    def get_absolute_url(self):
        return reverse("product_variantimage_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("product_variantimage_update", args=(self.pk,))

class PricingTier(models.Model):
    """
    base-tier will have basic purchase and selling price for the product-variants,
    consequent tiers can derive from base-tier and modify a set of price for the set of products
    """
    name = models.CharField(max_length=255)
    contact = models.ForeignKey('contact.Customer', on_delete=models.CASCADE)
    minimum_quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name}"

class Price(models.Model):
    """
    price for each product variant that will be used by stock in determining selling/purchasing
    price based on the tier the customer belongs to
    """
    product = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    contact = models.ForeignKey('contact.Customer', on_delete=models.CASCADE)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_tier = models.ForeignKey(PricingTier, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product} : {self.selling_price} {self.purchase_price}"

class Stock(models.Model):

    """
    represents stock for each product variant.this stock is used in sale/purchase purposes
    """

    created = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    reorderat = models.IntegerField(default=1)

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name = 'stocks'
    )

    objects = StockManager()

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        cb = self.current_balance()
        return f"{self.code} {cb['wt']} {cb['qty']}"

    def get_absolute_url(self):
        return reverse("product_stock_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("product_stock_update", args=(self.pk,))

    def get_pure_by_melting(self):
        bal = self.current_balance()
        return bal["wt"] * self.melting

    def get_pure_by_cost(self):
        bal = self.current_balance()
        return bal["wt"] * self.cost

    def audit(self):
        """
        get last audit cb,totalin,total out and then append following
        """
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
        cb_wt = ls_wt + (stock_in["wt"] - stock_out["wt"])
        cb_qty = ls_qty + (stock_in["qty"] - stock_out["qty"])

        return StockStatement.objects.create(
            stock=self,
            Closing_wt=cb_wt,
            Closing_qty=cb_qty,
            total_wt_in=stock_in["wt"],
            total_qty_in=stock_in["qty"],
            total_wt_out=stock_out["wt"],
            total_qty_out=stock_out["qty"],
        )

    def stock_in_txns(self, ls):
        """
        return all the In transactions since last audit"""
        st = self.stocktransaction_set.all()
        if ls:
            st = st.filter(created__gte=ls.created)
        st = st.filter(movement_type__in=["P", "SR", "AR", "AD"])

        return st.aggregate(
            qty=Coalesce(
                Sum("quantity", output_field=models.IntegerField()), 0),
            wt=Coalesce(
                Sum("weight", output_field=models.DecimalField()), Decimal(0.0)
            ),
        )

    def stock_out_txns(self, ls):
        """
        return all Out Transactions since last audit
        """
        st = self.stocktransaction_set.all()
        if ls:
            st = st.filter(created__gte=ls.created)
        st = st.filter(movement_type__in=["PR", "S", "A", "RM"])

        return st.aggregate(
            qty=Coalesce(
                Sum("quantity", output_field=models.IntegerField()), 0),
            wt=Coalesce(
                Sum("weight", output_field=models.DecimalField()), Decimal(0.0)
            ),
        )

    def current_balance(self):
        """
         compute balance from last audit and append following
         """
        bal = {}
        Closing_wt:Decimal = 0
        Closing_qty:int = 0

        try:
            ls = self.stockstatement_set.latest()
            Closing_wt = ls.Closing_wt
            Closing_qty = ls.Closing_qty
            
        except StockStatement.DoesNotExist:
            ls = None
            
        in_txns = self.stock_in_txns(ls)
        out_txns = self.stock_out_txns(ls)
        bal["wt"] = Closing_wt + (in_txns["wt"] - out_txns["wt"])
        bal["qty"] = Closing_qty + (in_txns["qty"] - out_txns["qty"])
        return bal

    def get_age(self):
        """
        return get average of purchase date from today and average of sale dates from today then sub both
        """
        pass

    def transact(self, weight, quantity, journal, movement_type):
        """
        Modifies weight and quantity associated with the stock based on movement type
        Returns none
        """
        StockTransaction.objects.create(
            journal=journal,
            stock=self,
            weight=weight,
            quantity=quantity,
            movement_type=movement_type,
        )
        self.update_status()

    def merge_lots(self):
        """
            merges all lots in to individual lots representing this stock of its product variant.
            single operation to merge lots blindly.
            merge only non huid/non-unique lots
            
        """
        all_lots = self.lots.exclude(is_unique = True)
        current = all_lots.current_balance()
        new_lot = StockLot.objects.create(wt = current.wt,qty = current.qty,
                                          stock = current.stock)
        new_lot.transact(wt = current.wt,qty = current.qty,journal = None,
                        movement_type = 'AD')
        for i in all_lots:
            i.transact(wt = current.wt,qty = current.qty,journal = None,
                        movement_type = 'RM')
        return new_lot


class StockLot(models.Model):
    """
    StockLot core idea: 
        1 productV has many lots and all lots[productv] reference one stock
        on purchase add to stocklot from purchase_item 
        on sale choose from stocklot from sale_item
    """
    # should this be mptt?

    created = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    qty = models.IntegerField(default=0)
    wt = models.DecimalField(max_digits=10, decimal_places=3)
    barcode = models.CharField(
        max_length=155, null=True, blank=True, unique=True, editable=False
    )
    huid = models.CharField(max_length=6, null=True, blank=True, unique=True)
    stock_code = models.CharField(max_length=4)
    purchase_touch = models.DecimalField(max_digits=10, decimal_places=3)
    purchase_rate = models.DecimalField(max_digits=10, decimal_places=3,
                                        null=True, blank=True)
    is_unique = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=(
        ('Empty', 'Empty'), ('Available', 'Available'), ('Sold', 'Sold'),
        ('Approval', 'Approval'), ('Return',
                                   'Return'), ('Merged', 'Merged'),
    ),
        default='Empty')

    # related fields
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE,
                              related_name='lots'
                              )
    # redundant aint it?
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='stock_lots'
    )
    # not sure
    # purchase = models.ForeignKey('Purchase.Invoice', on_delete=models.SET_NULL,
    #                              null=True, blank=True)
    # sale = models.ForeignKey('Sales.Invoice', on_delete=models.SET_NULL,
    #                          null=True, blank=True)

    objects = StockLotManager()

    def __str__(self):
        return f"{self.barcode} | {self.huid}"

    def save(self, *args, **kwargs):
        super(StockLot, self).save(*args, **kwargs)
        if not self.barcode:
            self.barcode = encode(self.pk)
            self.save()

    def update_status(self):
        cb = self.current_balance()
        if cb['wt'] <= 0.0 or cb['qty'] <=0:
            self.status = "Empty"
        else:
            self.status = "Available"
        self.save()

    def audit(self):

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
        cb_wt = ls_wt + (stock_in['wt'] - stock_out['wt'])
        cb_qty = ls_qty + (stock_in['qty'] - stock_out['qty'])

        return StockStatement.objects.create(stock=self.stock,
                                             stock_batch=self,
                                             Closing_wt=cb_wt,
                                             Closing_qty=cb_qty,
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
            ls = self.stockstatement_set.latest()
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

    def transact(self, weight, quantity, journal, movement_type):
        """
        Modifies weight and quantity associated with the stock based on movement type
        Returns none
        """
        StockTransaction.objects.create(
            journal=journal,
            lot=self,
            weight=weight,
            quantity=quantity,
            movement_type=movement_type,
        )
        self.update_status()

    def merge(self, lot:int):
        """
        a lots qty and weight remains same troughout its life,
        any add/remove/merge/split on a lot is performed via transactions,
        and current balance of a lot is derived from transaction.
        
        Return : new_lot:StockLot
        """

        if self.variant != lot.variant or self.stock != lot.stock:
            raise Exception(
                "cannot merge lots from different variant or associated with different stock")

        new_lot = StockLot(variant=self.variant, wt=lot.wt +
                           self.wt, qty=lot.qty+self.qty)
        self.transact(self.wt,self.qty,journal = None,movement_type='RM')
        lot.transact(lot.wt,lot.qty,journal = None,movement_type='RM')
        new_lot.transact(
            self.wt + lot.wt, self.qty + lot.qty, journal = None, movement_type='AD')
        return new_lot

    def split(self, wt: Decimal, qty:int):
        """
        split a lot by creating a new lot and transfering the wt & qty to new lot
        """     
        if not self.is_unique and self.qty > qty and self.wt > wt:
            
            new_lot = StockLot(variant=self.variant,wt = wt,qty = qty)
            new_lot.transact(wt,qty,journal = None,movement_type='AD')
           
            self.transact(wt,qty,journal = None,movement_type='RM')

            return new_lot     
        raise Exception('Unique lots cant be split')

class Movement(models.Model):

    """ represents movement_type with direction of stock/lot transaction
    ex: [('purchase','+'),('purchase return','-'),('sales','-'),('sale return','+'),
        ('split','-'),('merge','+')]
    """
    id = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=30)
    direction = models.CharField(max_length=1, default='+')


class StockTransaction(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    quantity = models.IntegerField(default=0)
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    description = models.TextField()

    # relational Fields
    # user = models.ForeignKey(CustomUser)
    movement_type = models.ForeignKey(Movement, on_delete=models.CASCADE,default = 'P')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    lot = models.ForeignKey(StockLot, on_delete=models.CASCADE,default = 1)

    journal = models.ForeignKey(
        Journal, on_delete=models.CASCADE, null=True, blank=True, related_name="stxns"
    )

    class Meta:
        ordering = ("-created",)
        get_latest_by = ["created"]

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        return reverse("product_stocktransaction_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("product_stocktransaction_update", args=(self.pk,))


class StockStatement(models.Model):
    ss_method = (
        ("Auto", "Auto"),
        ("Physical", "Physical"),
    )
    method = models.CharField(max_length=20, choices=ss_method, default="Auto")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    lot = models.ForeignKey(StockLot, on_delete=models.CASCADE,null = True)

    created = models.DateTimeField(auto_now=True)
    Closing_wt = models.DecimalField(max_digits=14, decimal_places=3)
    Closing_qty = models.IntegerField()
    total_wt_in = models.DecimalField(
        max_digits=14, decimal_places=3, default=0.0)
    total_wt_out = models.DecimalField(
        max_digits=14, decimal_places=3, default=0.0)
    total_qty_in = models.IntegerField(default=0.0)
    total_qty_out = models.IntegerField(default=0.0)

    class Meta:
        ordering = ("created",)
        get_latest_by = ["created"]

    def __str__(self):
        return f"{self.stock} - qty:{self.Closing_qty} wt:{self.Closing_wt}"


class StockBalance(models.Model):
    stock = models.OneToOneField(
        Stock, on_delete=models.DO_NOTHING, primary_key=True)
    Closing_wt = models.DecimalField(max_digits=14, decimal_places=3)
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


class StockLotBalance(models.Model):

    lot = models.OneToOneField(
        StockLot, on_delete=models.DO_NOTHING, primary_key=True)
    Closing_wt = models.DecimalField(max_digits=14, decimal_places=3)
    Closing_qty = models.IntegerField()
    in_wt = models.DecimalField(max_digits=14, decimal_places=3, default=0.0)
    in_qty = models.IntegerField(default=0)
    out_wt = models.DecimalField(max_digits=14, decimal_places=3, default=0.0)
    out_qty = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'stockbatch_balance'

    def get_qty_bal(self):
        return self.Closing_qty + self.in_qty - self.out_qty

    def get_wt_bal(self):
        return self.Closing_wt + self.in_wt - self.out_wt
