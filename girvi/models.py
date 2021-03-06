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
from .managers import LoanManager,ReleasedManager,UnReleasedManager,ReleaseManager

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

    def get_series_count(self):
        return self.series_set.count()


class Series(models.Model):
    name = models.CharField(max_length=30,default ='',blank=True,unique=True)
    created = models.DateTimeField(auto_now_add = True,editable = False)
    last_updated = models.DateTimeField(auto_now = True)
    license = models.ForeignKey(License,on_delete = models.CASCADE)

    class Meta:
        ordering = ('created',)
        unique_together = ['license','name']

    def __str__(self):
        return f"Series {self.name}"

    def get_absolute_url(self):
        return reverse('girvi_license_series_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('girvi_license_series_update', args=(self.pk,))

    def loan_count(self):
        return self.loan_set.filter(release__isnull=True).count()

    def total_loan_amount(self):
        return self.loan_set.filter(release__isnull=True).aggregate(t=Sum('loanamount'))

    def total_gold_loan(self):
        return self.loan_set.filter(release__isnull=True,itemtype='Gold').aggregate(t=Sum('loanamount'))

    def total_silver_loan(self):
        return self.loan_set.filter(release__isnull=True,itemtype='Silver').aggregate(t=Sum('loanamount'))

    def total_gold_weight(self):
        return self.loan_set.filter(release__isnull=True,itemtype='Gold').aggregate(t=Sum('itemweight'))

    def total_silver_weight(self):
        return self.loan_set.filter(release__isnull=True,itemtype='Silver').aggregate(t=Sum('itemweight'))


class Loan(models.Model):

    # Fields
    lid = models.IntegerField(blank=True,null=True)
    loanid = models.CharField(max_length=255,unique=True)
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    itype=(
            ('Gold','Gold'),
            ('Silver','Silver'),
            ('Bronze','Bronze'))
    itemtype = models.CharField(max_length=30,choices=itype,default='Gold')
    itemdesc = models.TextField(max_length=100)
    itemweight = models.DecimalField(max_digits=10, decimal_places=2)
    itemvalue = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    loanamount = models.PositiveIntegerField()
    interestrate = models.PositiveSmallIntegerField(default = 2)
    interest = models.PositiveIntegerField()

    series = models.ForeignKey(Series,on_delete = models.CASCADE,
        blank=True,null = True,)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
    )

    # Managers
    # objects = models.Manager()
    objects = LoanManager()
    released = ReleasedManager()
    unreleased = UnReleasedManager()

    class Meta:
        ordering = ('series','lid')

    def __str__(self):
        return f"{self.loanid} - {self.loanamount}"

    def get_absolute_url(self):
        return reverse('girvi_loan_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('girvi_loan_update', args=(self.pk,))

    def noofmonths(self,date = datetime.datetime.now(timezone.utc)):
        cd = date #datetime.datetime.now()
        nom = (cd.year-self.created.year)*12 + cd.month - self.created.month
        if(nom<=0):
            return 0
        else:
            return nom
    @property
    def is_released(self):
        return hasattr(self,'release')

    def interestdue(self,date= datetime.datetime.now(timezone.utc)):
        if self.is_released :
            return 0
        else:
            return int(((self.loanamount)*self.noofmonths(date)*(self.interestrate))/100)

    def total(self):
        return self.interestdue() + float(self.loanamount)

    def get_total_adjustments(self):
        as_int =0
        as_amt =0
        for a in self.adjustments.all():
            if a.as_interest:
                as_int += a.amount_received
            else:
                as_amt +=a.amount_received
        data = {'int': as_int,'amt':as_amt}
        return data

    def due(self):
        a = self.get_total_adjustments()
        return self.loanamount + self.interestdue() - a['int'] - a['amt']

    def is_worth(self):
        return self.itemvalue<total

    def get_next(self):
        return Loan.objects.filter(series = self.series,lid__gt = self.lid).order_by('lid').first()

    def get_previous(self):
        return Loan.objects.filter(series = self.series,lid__lt = self.lid).order_by('lid').last()

    def save(self,*args,**kwargs):
        self.interest = self.interestdue()
        self.itemvalue = self.loanamount+500
        self.loanid = self.series.name + str(self.lid)
        super().save(*args,**kwargs)

class Adjustment(models.Model):
    created = models.DateTimeField(auto_now_add = True)
    amount_received = models.IntegerField(default =0)
    as_interest = models.BooleanField(default = True)
    loan = models.ForeignKey('girvi.Loan',on_delete = models.CASCADE,
                                related_name='adjustments')

    class Meta:
        ordering = ('created',)

    def __str__(self):
        return f"{self.amount_received}=>loan{self.loan}"
    def get_absolute_url(self):
        return reverse('girvi_adjustment_detail', args = (self.pk,))
    def get_update_url(self):
        return reverse('girvi_adjustments_update', args = (Self.pk,))

class Release(models.Model):

    # Fields
    releaseid = models.CharField(max_length=255,unique=True)
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    interestpaid = models.IntegerField(default=0)

    # Relationship Fields
    loan = models.OneToOneField(
        'girvi.Loan',
        on_delete=models.CASCADE, related_name="release"
    )
    objects = ReleaseManager
    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return u'%s' % self.releaseid

    def get_absolute_url(self):
        return reverse('girvi_release_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('girvi_release_update', args=(self.pk,))

    def total_received(self):
        return self.loan.loanamount + self.interestpaid
