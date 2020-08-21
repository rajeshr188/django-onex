from django.urls import reverse
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth import models as auth_models
from django.db import models
from contact.models import Customer
from product.models import ProductVariant,Stree
from django.utils import timezone
from django.db.models import Avg,Count,Sum,Func,F
# from django.contrib.postgres.indexes import BrinIndex
from mptt.models import TreeForeignKey
class Month(Func):
    function = 'EXTRACT'
    template = '%(function)s(MONTH from %(expressions)s)'
    output_field = models.IntegerField()

class Year(Func):
    function = 'EXTRACT'
    template = '%(function)s(YEAR from %(expressions)s)'
    output_field = models.IntegerField()

class Invoice(models.Model):

    # Fields
    created = models.DateTimeField(default=timezone.now,db_index=True)
    last_updated = models.DateTimeField(default=timezone.now)
    rate = models.PositiveSmallIntegerField(default=3000)
    btype_choices=(
            ("Cash","Cash"),
            ("Metal","Metal")
        )
    itype_choices=(
        ("Cash","Cash"),
        ("Credit","Credit")
    )
    balancetype = models.CharField(max_length=30,choices=btype_choices,default="Metal")
    paymenttype = models.CharField(max_length=30,choices=itype_choices,default="Credit")
    balance = models.DecimalField(max_digits=10, decimal_places=3)
    status_choices=(
                    ("Paid","Paid"),
                    ("Partially Paid","PartiallyPaid"),
                    ("Unpaid","Unpaid")
    )
    status=models.CharField(max_length=15,choices=status_choices,default="Unpaid")

    # Relationship Fields
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,related_name="invoicee"
    )

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f"{self.id}"

    def get_absolute_url(self):
        return reverse('sales_invoice_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('sales_invoice_update', args=(self.pk,))

    def get_weight(self):
        return self.invoiceitem_set.aggregate(t=Sum('weight'));

    def get_total_receipts(self):
        paid=self.receiptline_set.aggregate(t=Sum('amount'))
        return paid['t']

    def get_balance(self):
        if self.get_total_receipts() != None :
            return self.balance - self.get_total_receipts()
        return self.balance

class InvoiceItem(models.Model):

    # Fields
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    touch = models.PositiveSmallIntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=3)
    is_return = models.BooleanField(default=False,verbose_name='Return')
    quantity = models.IntegerField()
    makingcharge=models.DecimalField(max_digits=10,decimal_places=3,default=0)
    # Relationship Fields
    product = TreeForeignKey(
        Stree,
        on_delete=models.CASCADE
    )
    invoice = models.ForeignKey(
        'sales.Invoice',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ('-pk',)

    def __str__(self):
        return u'%s' % self.pk

    def get_absolute_url(self):
        return reverse('sales_invoiceitem_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('sales_invoiceitem_update', args=(self.pk,))

    def get_nettwt(self):
        return (self.weight * self.touch)/100

    def save(self,*args,**kwargs):
        super(InvoiceItem,self).save(*args,**kwargs)
        print(f"In Sale Modelform save() :")
        print(f"item is_return: {self.is_return} ")
        print(self.product.refresh_from_db())

        sold,created = Stree.objects.get_or_create(name='Sold')
        if not self.is_return:#if sold
            if self.product.tracking_type =='Lot':
                sold = sold.traverse_parellel_to(self.product)
                print(f"moving { self.weight} from {self.product.get_family()[0].name} {self.product.weight} to {sold.get_family()[0].name}")
                self.product.transfer(sold,self.quantity,self.weight)
                print(f"moved from {self.product.get_family()[0]} {self.product.weight} to {sold.get_family()[0]}")
            else:
                sold = sold.traverse_parellel_to(self.product,include_self=False)
                print(f"moving { self.weight} from {self.product.get_family()[0]} {self.product.weight} to {sold.get_family()[0]} {sold.weight}")
                self.product = self.product.move_to(sold,position='first-child')
        else:#if returned
            stock,created = Stree.objects.get_or_create(name='Stock')
            if self.product.tracking_type =='Lot':
                stock = stock.traverse_parellel_to(self.product)
                print(f"moving { self.weight} from {self.product.get_family()[0]} {self.product.weight} to {stock.get_family()[0]} {stock.weight}")
                self.product.transfer(stock,self.quantity,self.weight)
                print(f"moved { self.weight} from {self.product.get_family()[0]} {self.product.weight} to {stock.get_family()[0]} {stock.weight}")
            else:
                stock = stock.traverse_parellel_to(self.product,include_self=False)
                print(f"moving { self.weight} from {self.product.get_family()[0]} {self.product.weight} to {stock.get_family()[0]} {stock.weight}")
                self.product = self.product.move_to(stock,position='first-child')

        # print(f"item node : {item.product.get_family()} wt : {item.product.weight} {item.product.barcode}")
        # print(f"sold node : {sold.get_family()} wt : {sold.weight} {sold.barcode}")

class Receipt(models.Model):

    # Fields
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)
    btype_choices=(
                ("Cash","Cash"),
                ("Metal","Metal")
            )
    type = models.CharField(max_length=30,verbose_name='Currency',choices=btype_choices,default="Cash")
    rate= models.IntegerField(default=0)
    weight = models.DecimalField(max_digits=10,blank=True,decimal_places=3,default=0.0)
    touch = models.DecimalField(max_digits=10, decimal_places=2,blank=True,default=0.0)
    nettwt = models.DecimalField(max_digits=10,blank=True,decimal_places=3,default=0.0)
    total = models.DecimalField(max_digits=10, decimal_places=3)
    description = models.TextField(max_length=50,default="describe here")
    status_choices=(
                    ("Allotted","Allotted"),
                    ("Partially Allotted","PartiallyAllotted"),
                    ("Unallotted","Unallotted")
    )
    status=models.CharField(max_length=18,choices=status_choices,default="Unallotted")
    # Relationship Fields
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE, related_name="receivedfrom"
    )

    class Meta:
        ordering = ('-created',)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Call the "real" save() method.
        # print('insave')
        total_allotted=self.get_line_totals()
        if total_allotted is not None :
            if total_allotted == self.total:
                self.status="Allotted"
            else:
                self.status="Unallotted"
        super().save(*args, **kwargs)

    def __str__(self):
        return u'%s' % self.id

    def get_absolute_url(self):
        return reverse('sales_receipt_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('sales_receipt_update', args=(self.pk,))

    def get_line_totals(self):
        return self.receiptline_set.aggregate(t=Sum('amount'))['t']

class ReceiptLine(models.Model):

    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)
    amount= models.DecimalField(max_digits=10,decimal_places=3)
    #relationship Fields
    receipt = models.ForeignKey(Receipt,on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice,on_delete=models.CASCADE)

    def __str__(self):
        return u'%s' % self.id

    def get_absolute_url(self):
        return reverse('sales_receiptline_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('sales_receiptline_update', args=(self.pk,))
