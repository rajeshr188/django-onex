from django.urls import reverse
from django.db import models,transaction
from contact.models import Customer
from product.models import ProductVariant
from django.utils import timezone
from datetime import timedelta,date
from django.db.models import Sum,Q,Avg
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation
from product.models import Stock,StockTransaction,Attribute
from product.attributes import get_product_attributes_data
from dea.models import Journal,JournalTypes
from invoice.models import PaymentTerm
from moneyed import Money
# if not posted : delete/edit
#  if posted : !edit
#  delete any time
class PurchaseQueryset(models.QuerySet):
    def posted(self):
        return self.filter(posted = True)
    def unposted(self):
        return self.filter(posted = False)
    def gst(self):
        return self.filter(is_gst = True)
    def non_gst(self):
        return self.filter(is_gst = False)
    def total(self):
        return self.aggregate(
            cash=Sum('balance', filter=Q(balancetype='INR')),
            gold=Sum('balance', filter=Q(balancetype='USD')),
            silver=Sum('balance', filter=Q(balancetype='AUD')),
        )
    def today(self):
        return self.filter(created__date = date.today())
    def cur_month(self):
        return self.filter(created__month = date.today().month,
        created__year = date.today().year)
    def total_with_ratecut(self):
        return self.aggregate(
            cash=Sum('balance', filter=Q(balancetype='INR')),
            cash_g=Sum('balance', filter=Q(
                balancetype='INR', metaltype='Gold')),
            cash_s=Sum('balance', filter=Q(
                balancetype='INR', metaltype='Silver')),
            cash_g_nwt=Sum('net_wt', filter=Q(
                balancetype='INR', metaltype='Gold')),
            cash_s_nwt=Sum('net_wt', filter=Q(
                balancetype='INR', metaltype='Silver')),
            
            gold=Sum('balance', filter=Q(balancetype='USD')),
            silver=Sum('balance', filter=Q(balancetype='AUD')),
        )

    def today(self):
        return self.filter(created__date=date.today())
    
    def avg_rate(self):
        return self.aggregate(gold=Avg('rate', filter=Q(balancetype='INR', metaltype='Gold')),
                                silver=Avg('rate', filter=Q(balancetype='INR', metaltype='Silver')))

    def cur_month(self):
        return self.filter(created__month=date.today().month,
                           created__year=date.today().year)


class InvoiceManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('supplier','term')

class Invoice(models.Model):

    # Fields
    created = models.DateTimeField(default=timezone.now, db_index=True)
    updated = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'users.CustomUser', on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='purchased')
    rate = models.DecimalField(max_digits=10, decimal_places=3,default = 0)
    is_gst = models.BooleanField(default=False)
    posted = models.BooleanField(default=False)
    gross_wt = models.DecimalField(max_digits=14, decimal_places=4, 
                default=0.0)
    net_wt = models.DecimalField(max_digits=14, decimal_places=4,
                default=0.0)
    total = models.DecimalField(max_digits=14, decimal_places=4,
                default=0.0)
    discount = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)
    balance = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)

    class BType(models.TextChoices):
        CASH = 'INR',_("Cash"),
        GOLD = 'USD',_("Gold"),
        SILVER = 'AUD',_("Silver")
        
    metal_choices = (
        ("Gold", "Gold"),
        ("Silver", "Silver")
    )
    status_choices = (
        ("Paid", "Paid"),
        ("PartiallyPaid", "PartiallyPaid"),
        ("Unpaid", "Unpaid")
    )
    status = models.CharField(
        max_length=15, choices=status_choices, default="Unpaid")
    balancetype = models.CharField(
        max_length=30, choices=BType.choices, default=BType.CASH)
    metaltype = models.CharField(
        max_length=30,choices = metal_choices,default="Gold")
    due_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default = True)
    # Relationship Fields
    supplier = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="purchases"
    )
    term = models.ForeignKey(
        PaymentTerm, on_delete=models.CASCADE,
        related_name = 'purchase_term',
        )
    journals = GenericRelation(Journal,related_query_name ='purchase_doc')
    
    objects = InvoiceManager.from_queryset(PurchaseQueryset)()
    class Meta:
        ordering = ('id','created',)

    def __str__(self):
        return f"{self.id}"

    def get_absolute_url(self):
        return reverse('purchase_invoice_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('purchase_invoice_update', args=(self.pk,))

    def get_next(self):
        return Invoice.objects.filter(id__gt=self.id).order_by('id').first()

    def get_previous(self):
        return Invoice.objects.filter(id__lt=self.id).order_by('id').last()

    def get_gross_wt(self):
        return self.purchaseitems.aggregate(t=Sum('weight'))['t']

    def get_net_wt(self):
        return self.purchaseitems.aggregate(t=Sum('net_wt'))['t']
    
    def get_total_balance(self):
        return self.purchaseitems.aggregate(t= Sum('total'))['t']

    def get_total_payments(self):
        paid=self.paymentline_set.aggregate(t=Sum('amount'))
        return paid['t']
    
    @property
    def overdue_days(self):
        return (timezone.now().date() - self.due_date).days

    def get_balance(self):
        if self.get_total_payments() != None :
            return self.balance - self.get_total_payments()
        return self.total 

    def save(self, *args, **kwargs):
        
        self.due_date = self.created + timedelta(days=self.term.due_days)
        self.total += self.get_gst()

        super(Invoice, self).save(*args, **kwargs)

    def get_gst(self):
        return (self.balance *3)/100 if self.is_gst else 0
        
    def get_txns(self,jrnl = None):
        if not jrnl:
            jrnl = Journal.objects.create(type=JournalTypes.PJ,
                        content_object=self, desc='purchase')
        txns = {}
        from dea.models import Ledger
        ledgers = dict(list(Ledger.objects.values_list('name', 'id')))
        money = Money(self.balance, self.balancetype)
        try:
            self.supplier.account
        except:
            self.supplier.save()
        if self.is_gst:
            inv = ledgers["GST INV"]
            tax = Money(self.get_gst(), 'INR')
            amount = money + tax
        else:
            inv = ledgers["Non-GST INV"]
            amount = money
            tax = Money(0,'INR')

        lt = [{'ledgerno': ledgers['Sundry Creditors'],'ledgerno_dr':inv,'amount':money},
                  {'ledgerno': ledgers['Sundry Creditors'], 'ledgerno_dr': ledgers['Input IGST'], 'amount': tax}, ]
        at = [{'ledgerno': ledgers['Sundry Creditors'],'xacttypecode':'Dr','xacttypecode_ext':'CRPU',
                    'account':self.supplier.account.id, 'amount':amount}]
        txns['lt'] = lt
        txns['at'] = at
        return txns
    
    def get_st(self):
        return []

    @transaction.atomic()
    def post(self):
        if not self.posted:
 
            jrnl = Journal.objects.create(type = JournalTypes.PJ,
                    content_object=self,desc='purchase')

            for i in self.purchaseitems.all():
                i.post(jrnl)

            txns = self.get_txns()

            jrnl.transact(txns['lt'],txns['at'])
 
            self.posted = True
            self.save(update_fields=['posted'])
       
    @transaction.atomic()
    def unpost(self):
        if self.posted:  
            last_jrnl = self.journals.latest()
            jrnl = Journal.objects.create(
                    content_object=self,desc='purchase revert')
            jrnl.untransact(last_jrnl)
            for i in self.purchaseitems.all():
                i.unpost(jrnl)
            self.posted = False
            self.save(update_fields=['posted'])
        
class InvoiceItem(models.Model):
    # Fields
    huid = models.CharField(max_length = 6,null = True,blank = True,unique = True)
    quantity = models.IntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    touch = models.DecimalField(max_digits=10, decimal_places=3)
    net_wt = models.DecimalField( max_digits=10, decimal_places=3,default = 0)
    total = models.DecimalField(max_digits=10,decimal_places=3)
    is_return = models.BooleanField(default=False,verbose_name='Return')
    makingcharge=models.DecimalField(max_digits=10,decimal_places=3,blank = True,verbose_name='mc')
    # Relationship Fields
    product = models.ForeignKey(
        ProductVariant,on_delete=models.CASCADE,
        related_name="products")
    invoice = models.ForeignKey(
        'purchase.Invoice',on_delete=models.CASCADE, 
        related_name="purchaseitems")

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

    @transaction.atomic()
    def post(self,journal):
        if not self.is_return:
            stock,created = Stock.objects.get_or_create(
                    variant=self.product, tracking_type='Lot')
            if created :
                stock.huid = self.huid
                attributes = get_product_attributes_data(
                              self.product.product)
                purity = Attribute.objects.get(name='Purity')
                stock.melting = int(attributes[purity].name)
                stock.cost = self.touch
                stock.touch = stock.cost+2
                stock.wastage = 10
                stock.save()
            lot = stock.create_batch(self.weight,self.quantity,self.touch)
            #stock.add(stockbatch = lot,journal = journal,weight = self.weight,quantity =  self.quantity,activity_type = 'P')
            lot.add(journal = journal,weight = self.weight,quantity =  self.quantity,activity_type = 'P')
        else:
            stock = Stock.objects.get(name=self.product.name,
                        tracking_type="Lot")
            stock.remove(journal = journal,weight = self.weight,quantity = self.quantity,activity_type = 'PR')

    @transaction.atomic()
    def unpost(self,journal):
        if self.is_return:
            stock = Stock.objects.get(
                variant=self.product, tracking_type='Lot')
            stock.add(journal = journal,weight = self.weight,quantity = self.quantity,activity_type = 'P')
        else:
            stock = Stock.objects.get(
                variant=self.product, tracking_type='Lot')
            stock.remove(journal = journal,weight = self.weight,quantity = self.quantity,activity_type ='PR')
            
class Payment(models.Model):

    # Fields
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now_add=True,editable = False)
    created_by = models.ForeignKey(
        'users.CustomUser', on_delete=models.CASCADE,
        null=True, blank=True)

    class BType(models.TextChoices):
        CASH = 'INR', _("Cash"),
        GOLD = 'USD', _("Gold"),
        SILVER = 'AUD', _("Silver")

    type = models.CharField(max_length=30,verbose_name='Currency',
            choices=BType.choices,default=BType.CASH)
    rate= models.IntegerField(default=0)
    total = models.DecimalField(max_digits=10, decimal_places=3)
    description = models.TextField(max_length=100)
    status_choices = (("Allotted","Allotted"),
                        ("Partially Allotted","PartiallyAllotted"),
                        ("Unallotted","Unallotted"), )
    status=models.CharField(max_length=18,choices=status_choices,
                    default="Unallotted")
    posted = models.BooleanField(default = False)
    is_active = models.BooleanField(default=True)
    journals = GenericRelation(Journal,related_query_name='payment_doc')
    # Relationship Fields
    supplier = models.ForeignKey(Customer,
        on_delete=models.CASCADE, related_name="payments")

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return u'%s' % self.id

    def get_absolute_url(self):
        return reverse('purchase_payment_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('purchase_payment_update', args=(self.pk,))

    def get_line_totals(self):
        return self.paymentline_set.aggregate(t=Sum('amount'))['t']

    def update_status(self):
        total_allotted=self.get_line_totals()
        if total_allotted is not None :
            if total_allotted == self.total:
                self.status="Allotted"
            else:
                self.status="Unallotted"
        self.save()

    def allot(self):
        print(f"allotting payment {self.id} type:{self.type} amount{self.total}")
        invpaid = 0 if self.get_line_totals() is None else self.get_line_totals()
        print(f" invpaid : {invpaid}")
        remaining_amount = self.total - invpaid
        print(f"remaining : {remaining_amount}")
        try:
            invtopay = Invoice.objects.filter(supplier = self.supplier,
                        balancetype = self.type,posted = True,balance__gte = 0)\
                            .exclude(status = "Paid").order_by("created")
        except IndexError:
            invtopay = None
        print(f" invtopay :{invtopay}")

        for i in invtopay:
            print(f"i:{i} bal:{i.get_balance()}")
            if remaining_amount<=0 : break
            bal=i.get_balance()
            if remaining_amount >= bal :
                remaining_amount -= bal
                PaymentLine.objects.create(payment=self,invoice=i,amount=bal)
                i.status="Paid"
            else :
                PaymentLine.objects.create(payment=self,invoice=i,amount=remaining_amount)
                i.status="PartiallyPaid"
                remaining_amount=0
            i.save()
        print('allotted payment')
        self.update_status()

    def deallot(self):
        self.paymentline_set.all().delete()
        self.update_status()

    def post(self):
        if not self.posted:
            from dea.models import Ledger
            ledgers = dict(list(Ledger.objects.values_list('name', 'id')))

            jrnl = Journal.objects.create(type = JournalTypes.PY,
                content_object = self,
                desc = 'payment')
            
            money = Money(self.total, self.type)
            lt = [{'ledgerno':ledgers['Cash'],'ledgerno_dr':ledgers['Sundry Creditors'],'amount':money}]
            at = [{'ledgerno':ledgers['Sundry Creditors'],'xacttypecode':'Cr','xacttypecode_ext':'PYT',
                    'account':self.supplier.account.id,'amount':money}]
            jrnl.transact(lt,at)
            self.posted = True
            self.save(update_fields = ['posted'])

    def unpost(self):
        if self.posted:
            last_jrnl = self.journals.latest()
            jrnl = Journal.objects.create(
                content_object=self,
                desc='payment')
            jrnl.untransact(last_jrnl)
            self.posted = False
            self.save(update_fields=['posted'])

class PaymentItem(models.Model):
    weight = models.DecimalField(
        max_digits=10, blank=True, decimal_places=3, default=0.0)
    touch = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, default=0.0)
    nettwt = models.DecimalField(
        max_digits=10, blank=True, decimal_places=3, default=0.0)
    rate = models.IntegerField(default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=3)
    payment = models.ForeignKey(Payment,on_delete = models.CASCADE)

    def __str__(self):
        return self.amount
        
class PaymentLine(models.Model):

    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)
    amount=models.DecimalField(max_digits=10,decimal_places=3)
    #relationship Fields
    payment=models.ForeignKey(Payment,on_delete=models.CASCADE)
    invoice=models.ForeignKey(Invoice,on_delete=models.CASCADE)

    def __str__(self):
        return u'%s' % self.id

    def get_absolute_url(self):
        return reverse('purchase_paymentline_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('purchase_paymentline_update', args=(self.pk,))
