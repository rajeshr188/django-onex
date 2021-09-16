from dea.models import Journal,JournalTypes
from django.urls import reverse
from decimal import Decimal
from django.db import models,transaction
from contact.models import Customer
import datetime
from django.utils import timezone
from django.db.models import Sum,Q
from django.contrib.contenttypes.fields import GenericRelation
import qrcode
import qrcode.image.svg
from qrcode.image.pure import PymagingImage
from io import BytesIO
from moneyed import Money
# class Month(Func):
#     function = 'EXTRACT'
#     template = '%(function)s(MONTH from %(expressions)s)'
#     output_field = models.IntegerField()

# class Year(Func):
#     function = 'EXTRACT'
#     template = '%(function)s(YEAR from %(expressions)s)'
#     output_field = models.IntegerField()


class LoanQuerySet(models.QuerySet):
    def posted(self):
        return self.filter(posted=True)

    def unposted(self):
        return self.filter(posted=False)

    def released(self):
        return self.filter(release__isnull=False)

    def unreleased(self):
        return self.filter(release__isnull=True)

    def total(self):
        return self.aggregate(
            total=Sum('loanamount'),
            gold=Sum('loanamount', filter=Q(itemtype='Gold')),
            silver=Sum('loanamount', filter=Q(itemtype='Silver')),
            bronze=Sum('loanamount', filter=Q(itemtype='Bronze'))
        )
    def interestdue(self):
        return self.aggregate(t = Sum('interest'))

class LoanManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('series', 'release', 'customer')

class ReleasedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(release__isnull=False)

class UnReleasedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(release__isnull=True)

class ReleaseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('loan')

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
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('created',)
        unique_together = ['license','name']

    def __str__(self):
        return f"Series {self.name}"

    def get_absolute_url(self):
        return reverse('girvi_license_series_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('girvi_license_series_update', args=(self.pk,))
    
    def activate(self):
        self.is_active = not self.is_active
        self.save(update_fields=['is_active'])

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

# to-do seperate loanitems from loan normalize
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
    posted = models.BooleanField(default = False)
    journals = GenericRelation(Journal,related_query_name='loan_doc')

    # Managers
    objects = LoanManager()
    released = ReleasedManager()
    unreleased = UnReleasedManager()
    lqs = LoanQuerySet.as_manager()

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
        return 1 if nom<=0 else nom-1

    @property
    def get_qr(self):
        factory = qrcode.image.svg.SvgImage
        img = qrcode.make(data=self.lid,
                          image_factory=factory, box_size=20)
        stream = BytesIO()
        img.save(stream)
        svg = stream.getvalue().decode()
        return svg 

    @property
    def is_released(self):
        return hasattr(self,'release')
    
    def interest_amt(self):
        return round(Decimal(self.loanamount * (self.interestrate)/100),3)

    def interestdue(self,date= datetime.datetime.now(timezone.utc)):
        if self.is_released :
            return Decimal(0)
        else:
            return self.interest_amt()*self.noofmonths(date)

    def total(self):
        return self.interestdue() + self.loanamount

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
        return self.itemvalue<self.total

    def get_next(self):
        return Loan.objects.filter(series = self.series,lid__gt = self.lid).order_by('lid').first()

    def get_previous(self):
        return Loan.objects.filter(series = self.series,lid__lt = self.lid).order_by('lid').last()

    @transaction.atomic()
    def post(self):
        # get contact.Account
        try:
            self.customer.account
        except:
            self.customer.save()
        amount = Money(self.loanamount,'INR')
        interest = Money(self.interest_amt(),'INR')
        if self.customer.type == 'Su':
            print (self.customer.type)
            jrnl = Journal.objects.create(type = JournalTypes.LT,
                content_object = self,desc = 'Loan Taken')
            lt = [{'ledgerno': 'Loans', 'ledgerno_dr': 'Cash',
                     'amount': amount},
                    {'ledgerno': 'Cash', 'ledgerno_dr': 'Interest Paid',
                      'amount': amount}, ]
            at = [{'ledgerno': 'Loans', 'Xacttypecode': 'Dr', 'xacttypecode_ext': 'LT',
                     'account': self.customer.account,'amount': amount},
                    {'ledgerno': 'Interest Payable', 'xacttypecode': 'Cr', 'xacttypecode_ext': 'IP',
                              'account': self.customer.account, 'amount': amount}]
        else:
            jrnl = Journal.objects.create(type = JournalTypes.LG,
                content_object=self,desc = 'Loan Given')
            lt = [{'ledgerno': 'Cash', 'ledgerno_dr': 'Loans & Advances',
                     'amount':amount},
                    {'ledgerno': 'Interest Received', 'ledgerno_dr': 'Cash',
                     'amount': interest}, ]
            at = [{'ledgerno': 'Loans & Advances', 'xacttypecode': 'Cr', 'xacttypecode_ext': 'LG',
                    'account':self.customer.account,'amount':amount},
                    {'ledgerno': 'Interest Received', 'xacttypecode': 'Dr', 'xacttypecode_ext': 'IR',
                    'account': self.customer.account, 'amount': interest}]
        jrnl.transact(lt,at)
         
        self.posted = True
        self.save(update_fields=['posted'])

    @transaction.atomic()
    def unpost(self):
        # delete journals if accounts and ledger not closed
        last_jrnl = self.journals.latest()
        if self.customer.type == 'Su':
            l_jrnl = Journal.objects.create(
                content_object=self,desc='Loan Taken Revert')
        else:
            l_jrnl = Journal.objects.create(
                content_object=self,desc='Loan Given Revert')
        l_jrnl.untransact(last_jrnl)
        # i_jrnl.untransact()
        self.posted = False
        self.save(update_fields = ['posted'])
    
    def save(self,*args,**kwargs):
        if not self.pk:
            self.itemvalue = self.loanamount+500
        self.loanid = self.series.name + str(self.lid)
        self.interest = self.interestdue()
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
        return reverse('girvi_adjustments_update', args = (self.pk,))

class LoanStatement(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    loan = models.ForeignKey(Loan,on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.created}"

class Release(models.Model):

    # Fields
    releaseid = models.CharField(max_length=255,unique=True)
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    interestpaid = models.IntegerField(default=0)
    posted = models.BooleanField(default = False)
    # Relationship Fields
    loan = models.OneToOneField(
        'girvi.Loan',
        on_delete=models.CASCADE, related_name="release"
    )
    journals = GenericRelation(Journal,related_query_name='release_doc')
    # manager
    objects = ReleaseManager()

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
    
    def post(self):
        amount = Money(self.loan.loanamount, 'INR')
        interest = Money(self.interestpaid, 'INR')
        if self.customer.type == 'Su':
            jrnl = Journal.objects.create(
                content_object=self, desc='Loan Repaid')
            lt = [{'ledgerno': 'Cash', 'ledgerno_dr': 'Loans',
                     'amount': amount},
                    {'ledgerno': 'Cash', 'ledgerno_dr': 'Interest Paid',
                     'amount': amount}, ]
            at = [{'ledgerno': 'Loans', 'xacttypecode': 'Cr', 'xacttypecode_ext': 'LP',
                     'account': self.customer.account, 'amount': amount},
                    {'ledgerno': 'Interest Payable', 'xacttypecode': 'Cr', 'xacttypecode_ext': 'IP',
                     'account': self.customer.account, 'amount': amount}]  
        else:
            jrnl = Journal.objects.create(
                content_object=self, desc='Loan Released')
            lt = [{'ledgerno': 'Loans & Advances', 'ledgerno_dr': 'Cash',
                     'amount': amount},
                  {'ledgerno': 'Interest Received', 'ledgerno_dr': 'Cash',
                      'amount': amount}, ]
            at = [{'ledgerno': 'Loans & Advances', 'xacttypecode': 'Dr', 'xacttypecode_ext': 'LR',
                    'account': self.customer.account, 'amount': amount},
                  {'ledgerno': 'Interest Received', 'xacttypecode': 'Dr', 'xacttypecode_ext': 'IR',
                   'account': self.customer.account, 'amount': interest}]
        jrnl.transact(lt, at)
        
        self.posted = True
        self.save(update_fields=['posted'])

    def unpost(self):
        last_jrnl = self.journals.latest()
        if self.loan.customer.type == 'Su':
            jrnl = Journal.objects.create(
                content_object=self,desc='Loan Repaid Revert')
        else:
            jrnl = Journal.objects.create(
                content_object=self,desc='Loan Released Revert')
        jrnl.untransact(last_jrnl)
        self.posted = False
        self.save(update_fields='posted')
