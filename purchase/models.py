from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

from django.db import models,transaction
from contact.models import Customer
from product.models import ProductVariant
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum

from django.contrib.contenttypes.fields import GenericRelation
from product.models import Stock,StockTransaction,Attribute
from product.attributes import get_product_attributes_data
from dea.models import Journal, LedgerStatement,PurchaseJournal,PaymentJournal
from invoice.models import PaymentTerm
# purchase can be deleted only if unposted or posted and paid 
# purchase can be posted/unposted only if purchase.created > latest audit
class Invoice(models.Model):

    # Fields
    created = models.DateTimeField(default=timezone.now, db_index=True)
    last_updated = models.DateTimeField(auto_now_add=True)
    rate = models.DecimalField(max_digits=10, decimal_places=3)
    is_gst = models.BooleanField(default=False)
    posted = models.BooleanField(default=False)
    gross_wt = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    net_wt = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)
    discount = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    balance = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    btype_choices = (
        ("Cash", "Cash"),
        ("Gold", "Gold"),
        ("Silver", "Silver"),
    )

    status_choices = (
        ("Paid", "Paid"),
        ("PartiallyPaid", "PartiallyPaid"),
        ("Unpaid", "Unpaid")
    )
    status = models.CharField(
        max_length=15, choices=status_choices, default="Unpaid")
    balancetype = models.CharField(
        max_length=30, choices=btype_choices, default="Cash")
 
    due_date = models.DateField(null=True, blank=True)

    # Relationship Fields
    supplier = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="purchases"
    )
    term = models.ForeignKey(
        PaymentTerm, on_delete=models.SET_NULL,
        related_name = 'purchase_term',
        blank=True, null=True)
    journals = GenericRelation(Journal,related_query_name ='purchase_doc')
    stock_txns = GenericRelation(StockTransaction)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f"{self.id}"

    def get_absolute_url(self):
        return reverse('purchase_invoice_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('purchase_invoice_update', args=(self.pk,))

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
        return (timezone.now().date() - self.date_due).days

    def get_balance(self):
        if self.get_total_payments() != None :
            return self.balance - self.get_total_payments()
        return self.balance 

    # if not posted : delete/edit
    #  if posted : !edit
    #  if posted and paid : delete 
    #  if posted and unpaid : !delete
    def delete(self):
        if self.posted and self.get_balance() !=0:
            raise Exception("cant delete purchase if posted and unpaid")
        else:
            super(Invoice,self).delete()

    def save(self, *args, **kwargs):
        if self.balance <0 :
            self.status = "Paid"
        if self.term.due_days:
            self.due_date = self.created + timedelta(days=self.term.due_days)
        self.total = self.balance
        if self.is_gst:    
            self.total += self.get_gst()

        super(Invoice, self).save(*args, **kwargs)

    # cant post unpost once statement is created
    def get_gst(self):
        return (self.balance *3)/100
        

    @transaction.atomic()
    def post(self):
        try:
            self.supplier.account
        except:
            self.supplier.save()
        for i in self.purchaseitems.all():
                i.post()
        if self.balance >0 :
            jrnl = PurchaseJournal.objects.create(
                content_object=self,
                desc='purchase'
            )
        else:
            jrnl = PaymentJournal.objects.create(
                content_object=self,
                desc='purchase'
            )
        jrnl.transact()
        self.posted = True
        self.save(update_fields=['posted'])
       
    @transaction.atomic()
    def unpost(self):
        for i in self.purchaseitems.all():
                i.unpost()
        if self.balance>0:
            jrnl = PurchaseJournal.objects.create(
                content_object=self,
                desc='purchase revert'
            )
        else:
            jrnl = PaymentJournal.objects.create(
                content_object=self,
                desc='purchase revert'
            )
        jrnl.transact(revert = True)
        self.posted = False
        self.save(update_fields=['posted'])
        

class InvoiceItem(models.Model):
    # Fields
    quantity = models.IntegerField()
    # add melting here
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    touch = models.DecimalField(max_digits=10, decimal_places=3)
    net_wt = models.DecimalField( max_digits=10, decimal_places=3,default = 0)
    total = models.DecimalField(max_digits=10,decimal_places=3)
    is_return = models.BooleanField(default=False,verbose_name='Return')
    makingcharge=models.DecimalField(max_digits=10,decimal_places=3)
    # Relationship Fields
    product = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="products"
    )
    invoice = models.ForeignKey(
        'purchase.Invoice',
        on_delete=models.CASCADE, related_name="purchaseitems"
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

    @transaction.atomic()
    def post(self):
        if not self.is_return:
                stock,created = Stock.objects.get_or_create(
                    variant=self.product, tracking_type='Lot')
                if created:
                    
                    attributes = get_product_attributes_data(
                        self.product.product)
                    purity = Attribute.objects.get(name='Purity')
                    print(attributes)
                    stock.melting = int(attributes[purity].name)
                    stock.cost = self.touch
                    stock.touch = stock.cost+2
                    stock.wastage = 10
                    stock.save()
                stock.add(self.weight, self.quantity, self.invoice, 'P')
        else:
            stock = Stock.objects.get(name=self.product.name,
                        tracking_type="Lot")
            stock.remove(self.weight, self.quantity,
                         self.invoice, 'PR')

    @transaction.atomic()
    def unpost(self):
        if self.is_return:
            # add lot back to stock
            stock = Stock.objects.get(
                variant=self.product, tracking_type='Lot')
            stock.add(self.weight, self.quantity, self.invoice, 'P')
        else:
            stock = Stock.objects.get(
                variant=self.product, tracking_type='Lot')
            stock.remove(
                self.weight, self.quantity,
                cto=self.invoice,
                at='PR'
            )
            

class Payment(models.Model):

    # Fields
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)
    btype_choices=(
                ("Cash","Cash"),
                ("Gold","Gold"),
                ("silver","Silver")
            )
    type = models.CharField(max_length=30,verbose_name='Currency',choices=btype_choices,default="Cash")
    rate= models.IntegerField(default=0)
    total = models.DecimalField(max_digits=10, decimal_places=3)
    description = models.TextField(max_length=100)
    status_choices = (
                        ("Allotted","Allotted"),
                        ("Partially Allotted","PartiallyAllotted"),
                        ("Unallotted","Unallotted"),
                        )
    status=models.CharField(max_length=18,choices=status_choices,default="Unallotted")
    posted = models.BooleanField(default = False)
    journals = GenericRelation(Journal,related_query_name='payment_doc')
    # Relationship Fields
    supplier = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE, related_name="payments"
    )

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return u'%s' % self.id

    def get_absolute_url(self):
        return reverse('purchase_payment_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('purchase_payment_update', args=(self.pk,))

    # if not posted : delete/edit
    #  if posted : !edit
    #  if posted and allotted : delete
    #  if posted and unallotted : !delete
    def delete(self):
        if self.posted and self.status != 'Allotted':
            raise Exception("cant delete purchase if posted and unallotted")
        else:
            super(Payment, self).delete()

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
                                            balancetype = self.type,
                                            posted = True,balance__gte = 0)\
                                            .exclude(status = "Paid")\
                                            .order_by("created")
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
            jrnl = PaymentJournal.objects.create(
                content_object = self,
                desc = 'payment'
            )
            jrnl.transact()
        self.posted = True
        self.save(update_fields = ['posted'])

    def unpost(self):
        if self.posted:
            jrnl = PaymentJournal.objects.create(
                content_object=self,
                desc='payment'
            )
            jrnl.transact(revert = True)
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
