from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.shortcuts import reverse
from django.utils.text import slugify
from django_extensions.db.fields import AutoSlugField
from mptt.managers import TreeManager
from mptt.models import MPTTModel, TreeForeignKey
from versatileimagefield.fields import PPOIField, VersatileImageField

from product.attributes import get_product_attributes_data

from .stock import StockTransaction


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
        ins = st.filter(movement_type__in=["P", "SR", "AR"])
        i = {}
        o = {}
        if ins.exists():
            i = ins.aggregate(wt=Sum("weight"), qty=Sum("quantity"))

        else:
            i["wt"] = 0
            i["qty"] = 0
        out = st.filter(movement_type__in=["S", "PR", "A"])
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
    image = VersatileImageField(upload_to="product/", ppoi_field="ppoi", blank=False)
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
