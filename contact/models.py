import decimal
from django.urls import reverse
from django.db.models import Count,Sum
from django.db.models.functions import Coalesce
from itertools import chain
# from phonenumber_field.modelfields import PhoneNumberField
from django.db import models
from itertools import tee, islice, chain
from dateutil import relativedelta
from django.utils import timezone

# class Contacts(models.Model):
#     created = models.DateTimeField(default = timezone.now)
#     updated = models.DateTimeField(auto_now = True)
#     name = models.CharField(max_length = 30)
#     phoneno = models.CharField(max_length = 12)
#     address = models.TextField()
#     ras=(('S/o','S/o'),('D/o','D/o'),('W/o','W/o'),('R/o','R/o'))
#     relatedas = models.CharField(max_length=5,choices=ras,default='S/o')
#     relatedto = models.CharField(max_length=30,blank=True)
#     area = models.CharField(max_length=50,blank=True)
#
#     def __str__(self):
#         return self.name
#
# class Firm(models.Model):
#     name = models.CharField(max_length = 30)
#     GSTNO = models.CharField(max_length = 30)
#     contact = models.OneToOneField(Contacts,on_delete=models.CASCADE)
#
#     def __str__(self):
#         return self.name
#
# class Customer(Contacts):
#     choices = (('Retail','Retail'),
#                 ('Wholesale','Wholesale'))
#     customer_type = models.CharField(max_length=10,choices=choices,default='Retail')
#
# class Supplier(Contacts):
#     initial = models.CharField(max_length = 10)

# use proxy here
class Customer(models.Model):

    # Fields
    name = models.CharField(max_length=255)
    firstname = models.CharField(max_length =255,blank = True)
    lastname = models.CharField(max_length =255,blank = True)
    gender = models.CharField( max_length = 1,
                                choices = (('M','M'),('F','F'),('N','N')),
                                default = 'M')
    religion = models.CharField(max_length = 10,choices = (
                                ('Hindu','Hindu'),('Muslim','Muslim'),
                                ('Christian','Christian'),('Atheist','Atheist')
                                ),default = 'Hindu' )
    pic = models.ImageField(upload_to='contacts/customer/pic/',null=True,blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    phonenumber = models.CharField(max_length=15,default='911',verbose_name='Contact')
    Address = models.TextField(max_length=100,blank=True)
    ctype = (('Wh','Wholesale'),('Re','Retail'),('Su','Supplier'))
    type = models.CharField(max_length=30,choices=ctype,default='Re')
    ras = (('S/o','S/o'),('D/o','D/o'),('W/o','W/o'),('R/o','R/o'))
    relatedas = models.CharField(max_length=5,choices=ras,default='S/o')
    relatedto = models.CharField(max_length=30,blank=True)
    area = models.CharField(max_length=50,blank=True)
    active = models.BooleanField(blank = True,default = True)

    class Meta:
        ordering = ('-created','name','relatedto')
        unique_together = ('name','relatedas','relatedto')

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
        amount=self.loan_set.aggregate(total=Coalesce(Sum('loanamount'),0))
        return amount['total']

    def get_total_interest_due(self):
        total_int = 0
        for i in self.get_loans:
            total_int += i.interestdue()
        return total_int
        
    @property
    def get_loans_count(self):
        return self.loan_set.count()

    def get_religion_count(self):
        return self.values('religion').annotate(Count('religion')).order_by('religion')

    def get_interestdue(self):
        return self.loan_set.aggregate(total=Sum('interest'))

    def get_gold_weight(self):
        gold=self.loan_set.filter(itemtype='Gold').aggregate(total=Sum('itemweight'))
        return gold['total']

    def get_silver_weight(self):
        silver=self.loan_set.filter(itemtype='Silver').aggregate(total=Sum('itemweight'))
        return silver['total']

    def get_release_average(self):
        no_of_months =0
        for i in self.loan_set.filter(release__isnull = False).all():
            delta= relativedelta.relativedelta(i.release.created,i.created)
            no_of_months += delta.years *12 + delta.months

        for i in self.loan_set.filter(release__isnull = True).all():
            delta = relativedelta.relativedelta(timezone.now(),i.created)
            no_of_months += delta.years*12 + delta.months

        return round(no_of_months / self.loan_set.count()) if self.loan_set.count() else 0

    # sales queries
    def get_sales_invoice(self):
        return self.sales.all()

    def get_total_invoice_cash(self):
        return self.sales.filter(balancetype="Cash").\
                aggregate(total=Coalesce(Sum('balance',output_field = models.DecimalField()),decimal.Decimal(0.0)))['total']

    def get_total_invoice_metal(self):
        return self.sales.filter(balancetype="Gold").\
            aggregate(total=Coalesce(
                Sum('balance', output_field=models.DecimalField()), decimal.Decimal(0.0)))

    def get_unpaid(self):
        return self.sales.exclude(status="Paid")

    def get_unpaid_cash(self):
        return self.get_unpaid().filter(balancetype="Cash")\
                .values('created','id','balance')

    def get_unpaid_cash_total(self):
        return self.get_unpaid_cash()\
                .aggregate(total=Coalesce(Sum('balance'),decimal.Decimal(0)))['total']

    def get_unpaid_metal(self):
        return self.get_unpaid().filter(balancetype="Metal")\
                .values('created','id','balance')

    def get_unpaid_metal_total(self):
        return self.get_unpaid_metal()\
                .aggregate(total=Coalesce(Sum('balance'),decimal.Decimal(0)))['total']

    def get_total_invoice_paid_cash(self):
        pass

    def get_total_invoice_paid_metal(self):
        pass

    def get_cash_receipts_total(self):
        return self.receipts.filter(type='Cash').aggregate(
                                            total = Sum('total'))['total']

    def get_metal_receipts_total(self):
        return self.receipts.filter(type='Metal').\
                    aggregate(total = Coalesce(Sum('total'),decimal.Decimal(0)))['total']

    def get_metal_balance(self):
        return self.get_total_invoice_metal() - self.get_metal_receipts_total()

    def get_cash_balance(self):
        return self.get_total_invoice_cash() - self.get_cash_receipts_total()

    def get_receipts(self):
        return self.receipts.all()

    def reallot_receipts(self):
        receipts = self.get_receipts()
        for i in receipts:
            i.deallot()
        for i in receipts:
            i.allot()
    
    def reallot_payments(self):
        payments = self.payments.all()
        for i in payments:
            i.deallot()
        for i in payments:
            i.allot()

    def previous_and_next(self,some_iterable):
        prevs, items, nexts = tee(some_iterable, 3)
        prevs = chain([None], prevs)
        nexts = chain(islice(nexts, 1, None), [None])
        return zip(prevs, items, nexts)

    def get_all_txns(self):
        sales = self.sales.all().values()
        for s in sales:
            s['type'] = 'sale'

        receipts = self.receipts.all().values()
        for r in receipts:
            r['type'] = 'receipt'

        purchases = self.purchases.all().values()
        for p in purchases:
            p['type'] = 'purchase'

        payments = self.payments.all().values()
        for pay in payments:
            pay['type'] = 'payment'

        txn_list = sorted(
            chain(sales, receipts, purchases, payments),
            key=lambda i: i['created'],reverse=True)

        for prev,item,next in self.previous_and_next(txn_list):

            if item['type'] =='sale':
                if prev:
                    item['metal_bal'] = prev['metal_bal'] - item['balance']
                else:
                    item['metal_bal'] = item['balance']
            elif item['type'] == 'purchase':
                if prev:
                    item['metal_bal'] = prev['metal_bal'] + item['balance']
                else:
                    item['metal_bal'] = item['balance']
            elif item['type'] == 'receipt':
                if prev:
                    item['metal_bal'] = prev['metal_bal'] + item['total']
                else:
                    item['metal_bal'] = item['balance']
            elif item['type'] == 'payment':
                if prev:
                    item['metal_bal'] = prev['metal_bal'] - item['total']
                else:
                    item['metal_bal'] = item['total']

        return txn_list

