from django.urls import reverse
from django_extensions.db.fields import AutoSlugField
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import DecimalField
from django.db.models import IntegerField
from django.db.models import PositiveSmallIntegerField
from django.db.models import TextField
from django_extensions.db.fields import AutoSlugField
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth import models as auth_models
from django.db import models as models
from django_extensions.db import fields as extension_fields
from contact.models import Supplier
from product.models import ProductVariant
from django.utils import timezone
from django.db.models import Avg,Count,Sum

class Invoice(models.Model):

    # Fields
    slug = extension_fields.AutoSlugField(populate_from='id', blank=True)
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)
    rate = models.PositiveSmallIntegerField()
    btype_choices=(
            ("Cash","Cash"),
            ("Metal","Metal")
        )
    itype_choices=(
        ("Cash","Cash"),
        ("Credit","Credit")
    )
    balancetype = models.CharField(max_length=30,choices=btype_choices,default="Cash")
    paymenttype = models.CharField(max_length=30,choices=itype_choices,default="Cash")
    balance = models.DecimalField(max_digits=10, decimal_places=3)
    status_choices=(
                    ("Draft","Draft"),
                    ("Paid","Paid"),
                    ("Partially Paid","partiallyPaid"),
                    ("Unpaid","Unpaid")
    )
    status=models.CharField(max_length=15,choices=status_choices,default="Unpaid")

    # Relationship Fields
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE, related_name="suppliers"
    )

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f"{self.supplier} / {self.id} / {self.created.date()} / {self.get_balance()}"

    def get_absolute_url(self):
        return reverse('purchase_invoice_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('purchase_invoice_update', args=(self.slug,))

    def get_weight(self):
        return self.purchaseinvoices.aggregate(t=Sum('weight'));

    def get_total_payments(self):
        paid=self.paymentline_set.aggregate(t=Sum('amount'))
        return paid['t']

    def get_balance(self):
        if self.get_total_payments() != None :
            return self.balance - self.get_total_payments()
        return self.balance


class InvoiceItem(models.Model):

    # Fields
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    touch = models.PositiveSmallIntegerField()
    total = models.DecimalField(max_digits=10,decimal_places=3)
    is_return = models.BooleanField(default=False,verbose_name='Return')
    quantity = models.IntegerField()
    makingcharge=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    # Relationship Fields
    product = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE, related_name="products"
    )
    invoice = models.ForeignKey(
        'purchase.Invoice',
        on_delete=models.CASCADE, related_name="purchaseinvoices"
    )

    class Meta:
        ordering = ('-pk',)

    def __str__(self):
        return u'%s' % self.pk

    def get_absolute_url(self):
        return reverse('purchase_invoiceitem_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('purchase_invoiceitem_update', args=(self.pk,))

    def get_nettwt(self):
        return (self.weight * self.touch)/100


class Payment(models.Model):

    # Fields
    slug = extension_fields.AutoSlugField(populate_from='id', blank=True)
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)
    btype_choices=(
                ("Cash","Cash"),
                ("Metal","Metal")
            )
    type = models.CharField(max_length=30,verbose_name='Currency',choices=btype_choices,default="Cash")
    rate=IntegerField(default=0)
    weight = DecimalField(max_digits=10,blank=True,decimal_places=3,default=0.0)
    touch = DecimalField(max_digits=10, decimal_places=2,blank=True,default=0.0)
    nettwt = DecimalField(max_digits=10,blank=True,decimal_places=3,default=0.0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(max_length=100)

    # Relationship Fields
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE, related_name="supplier"
    )

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('purchase_payment_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('purchase_payment_update', args=(self.slug,))

class PaymentLine(models.Model):

    slug = extension_fields.AutoSlugField(populate_from='id', blank=True)
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)
    amount=models.DecimalField(max_digits=10,decimal_places=3)
    #relationship Fields
    payment=models.ForeignKey(Payment,on_delete=models.CASCADE)
    invoice=models.ForeignKey(Invoice,on_delete=models.CASCADE)

    def __str__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('purchase_paymentline_detail', args=(self.slug,))

    def get_update_url(self):
        return reverse('purchase_paymentline_update', args=(self.slug,))
