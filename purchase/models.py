from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

from django.db import models,transaction
from contact.models import Customer
from product.models import ProductVariant
from django.utils import timezone
from django.db.models import Sum

from django.contrib.contenttypes.fields import GenericRelation
from product.models import Stock,StockTransaction,Attribute
from product.attributes import get_product_attributes_data
from dea.models import Journal, LedgerStatement,PurchaseJournal

# purchase can be /unposted only if purchase.created > latest ledgerstatement
class Invoice(models.Model):

    # Fields
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now_add=True)
    rate = models.PositiveSmallIntegerField(default=5100)
    btype_choices=(
            ("Cash","Cash"),
            ("Gold","Gold"),
            ("Silver","Silver"),
        )
    itype_choices=(
        ("Cash","Cash"),
        ("Credit","Credit")
    )
    balancetype = models.CharField(max_length=30,choices=btype_choices,default="Cash")
    paymenttype = models.CharField(max_length=30,choices=itype_choices,default="Credit")
    balance = models.DecimalField(max_digits=10, decimal_places=3)
    status_choices=(
                    ("Paid","Paid"),
                    ("PartiallyPaid","PartiallyPaid"),
                    ("Unpaid","Unpaid")
    )
    status=models.CharField(max_length=15,choices=status_choices,default="Unpaid")

    # Relationship Fields
    supplier = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="purchases"
    )
    posted = models.BooleanField(default = False)
    journals = GenericRelation(Journal)
    stock_txns = GenericRelation(StockTransaction)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f"{self.id}"

    def get_absolute_url(self):
        return reverse('purchase_invoice_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('purchase_invoice_update', args=(self.pk,))

    def get_weight(self):
        return self.purchaseinvoices.aggregate(t=Sum('weight'));

    def get_total_payments(self):
        paid=self.paymentline_set.aggregate(t=Sum('amount'))
        return paid['t']

    def get_balance(self):
        if self.get_total_payments() != None :
            return self.balance - self.get_total_payments()
        return self.balance

    # if not posted : delete
    # if posted and paid : delete 
    #  if posted and unpaid : !delete
    def delete(self):
        if self.posted and self.get_balance() !=0:
            raise Exception("cant delete purchase if posted and unpaid")
        else:
            super(Invoice,self).delete()

    # cant post unpost once statement is created

    @transaction.atomic()
    def post(self):
        for i in self.purchaseitems.all():
            i.post()
        jrnl = PurchaseJournal.objects.create(
            content_object = self,
            type = Journal.Types.PJ,
            desc = 'purchase'
        )
        jrnl.purchase(self.supplier.account,self.balance,
                        self.paymenttype,self.balancetype)
        self.posted = True
        self.save(update_fields = ['posted'])

    @transaction.atomic()
    def unpost(self):
        try:
            ls = LedgerStatement.objects.latest()
        except:
            ls = None
        if ls and ls.created < self.created:
            for i in self.purchaseitems.all():
                i.unpost()
            self.stock_txns.clear()
            self.journals.clear()
            self.posted = False
            self.save(update_fields=['posted'])
        else:
            raise ValueError('cant unpost purchase created before latest audit')

class InvoiceItem(models.Model):
    # Fields
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    touch = models.DecimalField(max_digits=10, decimal_places=3)
    total = models.DecimalField(max_digits=10,decimal_places=3)
    is_return = models.BooleanField(default=False,verbose_name='Return')
    quantity = models.IntegerField()
    makingcharge=models.DecimalField(max_digits=10,decimal_places=3)
    # Relationship Fields
    product = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE, related_name="products"
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
            if 'Lot' in self.product.name:
                stock,created = Stock.objects.get_or_create(variant = self.product,
                                                    tracking_type = 'Lot',
                                                    )
                if created:
                    stock.barcode='je'+ str(stock.id)
                    attributes = get_product_attributes_data(self.product.product)
                    purity = Attribute.objects.get(name='Purity')
                    stock.melting = int(attributes[purity].name)
                    stock.cost = self.touch
                    stock.touch = stock.cost+2
                    stock.wastage = 10
                    stock.save()
                
                stock.add(self.weight,self.quantity,
                            self.invoice,'P')
            else:
                stock = Stock.objects.create(variant = self.product,
                                            tracking_type = 'Unique')

                stock.barcode='je'+ str(stock.id)
                attributes = get_product_attributes_data(self.product.product)
                purity = Attribute.objects.get(name='Purity')
                stock.melting = int(attributes[purity].name)
                stock.cost = self.touch
                stock.touch = stock.cost+2
                stock.wastage = 10
                stock.add(self.weight,self.quantity,
                            self.invoice,'P')

        else:
            # is return true
            if 'Lot' in self.product.name:
                stock = Stock.get(name = self.product.name)
                stock.remove(self.weight,self.quantity,
                                self.invoice,'PR')
            else:
                print("merge unique to lot before returning")

    @transaction.atomic()
    def unpost(self):
        if self.is_return:
            if 'Lot' in self.product.name:
                pass
            else :
                pass
        else:
            if 'Lot' in self.product.name:
                stock = Stock.objects.get(variant = self.product)
                stock.remove(
                self.weight,self.quantity,
                cto = self.invoice,
                at = 'PR'
                )
            else:
                # Pass the self we created in the snippet above
                ct = ContentType.objects.get_for_model(self.invoice)

                # Get the list of likes
                txns = StockTransaction.objects.filter(content_type=ct,
                                                    object_id=self.invoice.id,
                                                    # activity_type=StockTransaction.PURCHASE,
                                                    stock__weight = self.weight,
                                                    stock__quantity= self.quantity,
                                                    )

                txns[0].stock.remove(
                self.weight,self.quantity,
                cto = self.invoice,
                at = 'PR'
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
    weight = models.DecimalField(max_digits=10,blank=True,decimal_places=3,default=0.0)
    touch = models.DecimalField(max_digits=10, decimal_places=2,blank=True,default=0.0)
    nettwt = models.DecimalField(max_digits=10,blank=True,decimal_places=3,default=0.0)
    total = models.DecimalField(max_digits=10, decimal_places=3)
    description = models.TextField(max_length=100)
    status_choices = (
                        ("Allotted","Allotted"),
                        ("Partially Allotted","PartiallyAllotted"),
                        ("Unallotted","Unallotted"),
                        )
    status=models.CharField(max_length=18,choices=status_choices,default="Unallotted")
    posted = models.BooleanField(default = False)
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
                                                posted = True).exclude(
                                                status = "Paid"
                                                ).order_by("created")
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

    # def save(self,*args,**kwargs):
    #     if self.pk :
    #         self.deallot()
    #     super(Payment,self).save(*args,**kwargs)
    #     self.allot()

    def post(self):
        jrnl = PurchaseJournal.objects.create(
            content_object = self,
            type = Journal.Types.PJ,
            desc = 'payment'
        )
        jrnl.payment(self.supplier.account,self.total,
                        self.type)
        self.posted = True
        self.save(update_fields = ['posted'])

    def unpost(self):
        self.journals.clear()
        self.posted = False
        self.save(update_fields=['posted'])


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
