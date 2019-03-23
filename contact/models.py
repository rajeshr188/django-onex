from django.urls import reverse
from django.utils.text import slugify
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth import models as auth_models
from django_extensions.db import fields as extension_fields
from django.db.models import Avg,Count,Sum
# from phonenumber_field.modelfields import PhoneNumberField
from django.db import models
import uuid

class Customer(models.Model):

    # Fields
    name = models.CharField(max_length=255)
    pic=models.ImageField(upload_to='contacts/customer/pic/',null=True,blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    phonenumber = models.CharField(max_length=15,default='911')
    Address = models.TextField(max_length=100,blank=True)
    ctype=(('Wh','Wholesale'),('Re','Retail'))
    type = models.CharField(max_length=30,choices=ctype,default='Re')
    ras=(('S/o','S/o'),('D/o','D/o'),('W/o','W/o'),('R/o','R/o'))
    relatedas = models.CharField(max_length=5,choices=ras,default='S/o')
    relatedto = models.CharField(max_length=30,blank=True)
    area = models.CharField(max_length=50,blank=True)

    class Meta:
        ordering = ('-created',)
        unique_together = ('name','relatedto')

    def __str__(self):
        return f"{self.name} {self.relatedas} {self.relatedto} {self.phonenumber}"

    def get_absolute_url(self):
        return reverse('contact_customer_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('contact_customer_update', args=(self.pk,))
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

    def get_total_invoice_cash(self):
        return self.invoicee.filter(balancetype="Cash").aggregate(total=Sum('balance'))['total']

    def get_total_invoice_metal(self):
        return self.invoicee.filter(balancetype="Metal").aggregate(total=Sum('balance'))['total']

    def get_unpaid(self):
        return self.invoicee.exclude(status="Paid")

    def get_unpaid_cash(self):
        return self.get_unpaid().filter(balancetype="Cash").values('created','id','balance')

    def get_unpaid_cash_total(self):
        return self.get_unpaid_cash().aggregate(total=Sum('balance'))['total']

    def get_unpaid_metal(self):
        return self.get_unpaid().filter(balancetype="Metal").values('created','id','balance')

    def get_unpaid_metal_total(self):
        return self.get_unpaid_metal().aggregate(total=Sum('balance'))['total']

    def get_total_invoice_paid_cash(self):
        pass

    def get_total_invoice_paid_metal(self):
        pass

    def get_total_invoice_balance(self):
        pass

class Supplier(models.Model):

    # Fields
    name = models.CharField(max_length=255,unique=True)
    pic=models.ImageField(upload_to='contacts/supplier/pic/',null=True,blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    organisation = models.CharField(max_length=30)
    phonenumber = models.CharField(max_length=15)
    initial = models.CharField(max_length=30)


    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return u'%s' % self.id

    def get_absolute_url(self):
        return reverse('contact_supplier_detail', args=(self.pk,))


    def get_update_url(self):
        return reverse('contact_supplier_update', args=(self.pk,))
