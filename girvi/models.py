from django.urls import reverse
from django_extensions.db.fields import AutoSlugField
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import DecimalField
from django.db.models import IntegerField
from django.db.models import PositiveIntegerField
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
from contact.models import Customer
import datetime
from django.utils import timezone
from django.db.models import Avg,Count,Sum

class License(models.Model):

    # Fields
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    lt=(('PBL','Pawn Brokers License'),
            ('GST','Goods & Service Tax'))
    type = models.CharField(max_length=30,choices=lt,default='PBL')
    shopname = models.CharField(max_length=30)
    address = models.TextField(max_length=100)
    phonenumber = models.CharField(max_length=30)
    propreitor = models.CharField(max_length=30)


    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('girvi_license_detail', args=(self.slug,))

    def get_update_url(self):
        return reverse('girvi_license_update', args=(self.slug,))

    def loan_count(self):
        return self.loan_set.count()

    def total_loan_amount(self):
        return self.loan_set.aggregate(t=Sum('loanamount'))

    def total_gold_loan(self):
        return self.loan_set.filter(itemtype='Gold').aggregate(t=Sum('loanamount'))

    def total_silver_loan(self):
        return self.loan_set.filter(itemtype='Silver').aggregate(t=Sum('loanamount'))

    def total_gold_weight(self):
        return self.loan_set.filter(itemtype='Gold').aggregate(t=Sum('itemweight'))

    def total_silver_weight(self):
        return self.loan_set.filter(itemtype='Silver').aggregate(t=Sum('itemweight'))


class Loan(models.Model):

    # Fields
    loanid = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='loanid', blank=True)
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    itype=(
            ('Gold','Gold'),
            ('Silver','Silver'),
            ('Bronze','Bronze'),('O','Other'),)
    itemtype = models.CharField(max_length=30,choices=itype,default='Gold')
    itemdesc = models.TextField(max_length=30)
    itemweight = models.DecimalField(max_digits=10, decimal_places=2)
    itemvalue = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    loanamount = models.PositiveIntegerField()
    interestrate = models.PositiveSmallIntegerField()
    interest = models.PositiveIntegerField()

    # Relationship Fields
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE,
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('girvi_loan_detail', args=(self.slug,))

    def get_update_url(self):
        return reverse('girvi_loan_update', args=(self.slug,))

    def noofmonths(self):
        cd=datetime.datetime.now()
        nom=(cd.year-self.created.year)*12 +cd.month-self.created.month
        if(nom<=0):
            return 0
        else:
            return nom-1

    def interestdue(self):
        return float(((self.loanamount)*self.noofmonths()*(self.interestrate))/100)

    def total(self):
        return self.interestdue() + float(self.loanamount)

    def is_released(self):
        return hasattr(self,'release')

    def is_worth(self):
        return self.itemvalue<total

    def get_loan_amount(self):
        return self.aggregate(t=Sum('loanamount'))

    def save(self,*args,**kwargs):
        self.interest=self.interestdue()
        #self.loanamount=self.loanamount - Decimal(self.interest)
        # self.itemvalue=self.loanamount+500
        super().save(*args,**kwargs)


class Release(models.Model):

    # Fields
    releaseid = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='releaseid', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    interestpaid = models.IntegerField()

    # Relationship Fields
    loan = models.ForeignKey(
        'girvi.Loan',
        on_delete=models.CASCADE, related_name="release"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE, related_name="releasedby"
    )

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('girvi_release_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('girvi_release_update', args=(self.slug,))
