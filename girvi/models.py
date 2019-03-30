from django.urls import reverse
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth import models as auth_models
from django.db import models
from contact.models import Customer
import datetime
from django.utils import timezone
from django.db.models import Avg,Count,Sum,Func
from .managers import ReleasedManager,UnReleasedManager

class Month(Func):
    function = 'EXTRACT'
    template = '%(function)s(MONTH from %(expressions)s)'
    output_field = models.IntegerField()

class Year(Func):
    function = 'EXTRACT'
    template = '%(function)s(YEAR from %(expressions)s)'
    output_field = models.IntegerField()

class License(models.Model):

    # Fields
    name = models.CharField(max_length=255)
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
        return u'%s' % self.name

    def get_absolute_url(self):
        return reverse('girvi_license_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('girvi_license_update', args=(self.pk,))

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
    loanid = models.CharField(max_length=255,unique=True)
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    itype=(
            ('Gold','Gold'),
            ('Silver','Silver'),
            ('Bronze','Bronze'))
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

    # Managers
    objects = models.Manager()
    released = ReleasedManager()
    unreleased = UnReleasedManager()

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f"{self.loanid} - {self.loanamount}"

    def get_absolute_url(self):
        return reverse('girvi_loan_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('girvi_loan_update', args=(self.pk,))

    def noofmonths(self):
        cd=datetime.datetime.now()
        nom=(cd.year-self.created.year)*12 +cd.month-self.created.month
        if(nom<=0):
            return 0
        else:
            return nom-1

    def interestdue(self):
        if is_released(self) :
            return 0
        else:
            return float(((self.loanamount)*self.noofmonths()*(self.interestrate))/100)

    def total(self):
        return self.interestdue() + float(self.loanamount)

    def is_released(self):
        return hasattr(self,'release')

    def is_worth(self):
        return self.itemvalue<total

    def save(self,*args,**kwargs):
        self.interest=self.interestdue()
        self.itemvalue=self.loanamount+500
        super().save(*args,**kwargs)


class Release(models.Model):

    # Fields
    releaseid = models.CharField(max_length=255,unique=True)
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    interestpaid = models.IntegerField()

    # Relationship Fields
    loan = models.OneToOneField(
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
        return u'%s' % self.releaseid

    def get_absolute_url(self):
        return reverse('girvi_release_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('girvi_release_update', args=(self.pk,))

    def total_received(self):
        return self.loan.loanamount + self.interestpaid
