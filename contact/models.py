from django.urls import reverse
from django_extensions.db.fields import AutoSlugField
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import TextField
from django_extensions.db.fields import AutoSlugField
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth import models as auth_models
from django.db import models as models
from django_extensions.db import fields as extension_fields
from django.db.models import Avg,Count,Sum
# from phonenumber_field.modelfields import PhoneNumberField

class Customer(models.Model):

    # Fields
    name = models.CharField(max_length=255)
    pic=models.ImageField(upload_to='contacts/customer/pic/',null=True,blank=True)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    phonenumber = models.CharField(max_length=15)
    Address = models.TextField(max_length=100,blank=True)
    ctype=(('Wh','Wholesale'),('Re','Retail'))
    type = models.CharField(max_length=30,choices=ctype,default='Re')
    ras=(('S/o','S/o'),('D/o','D/o'),('W/o','W/o'),('R/o','R/o'))
    relatedas = models.CharField(max_length=5,choices=ras,default='S/o')
    relatedto = models.CharField(max_length=30,blank=True)
    area = models.CharField(max_length=50,blank=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f"{self.name} {self.relatedas} {self.relatedto} {self.phonenumber}"

    def get_absolute_url(self):
        return reverse('contact_customer_detail', args=(self.slug,))

    def get_update_url(self):
        return reverse('contact_customer_update', args=(self.slug,))
    @property
    def get_loans(self):
        return self.loan_set.all()

    def get_total_loanamount(self):
        amount=self.loan_set.aggregate(total=Sum('loanamount'))
        return amount['total']
    @property
    def get_loans_count(self):
        return self.loan_set.count()

    # def get_interestdue(Self):
    #     interestdue=self.loan_set.aggregate(total=Sum('interestdue'))
    def get_gold_weight(self):
        gold=self.loan_set.filter(itemtype='Gold').aggregate(total=Sum('itemweight'))
        return gold['total']

    def get_silver_weight(self):
        silver=self.loan_set.filter(itemtype='Silver').aggregate(total=Sum('itemweight'))
        return silver['total']

class Supplier(models.Model):

    # Fields
    name = models.CharField(max_length=255)
    pic=models.ImageField(upload_to='contacts/supplier/pic/',null=True,blank=True)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    organisation = models.CharField(max_length=30)
    phonenumber = models.CharField(max_length=15)
    initial = models.CharField(max_length=30)


    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('contact_supplier_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('contact_supplier_update', args=(self.slug,))
