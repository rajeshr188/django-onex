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
from datetime import date,timedelta
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

class Terms(models.Model):
    name = models.CharField(max_length = 30)
    description = models.TextField()
    due_days = models.PositiveSmallIntegerField()
    discount_days = models.PositiveSmallIntegerField()
    discount = models.DecimalField(max_digits = 10,decimal_places = 2)

    class Meta:
        ordering = ('due_days',)

    def __str__(self):
        return f"{self.name} ({self.due_days})"


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
    term = models.ForeignKey(Terms,on_delete = models.SET_NULL,blank = True,null = True)
    balance = models.DecimalField(max_digits=10, decimal_places=3)
    status_choices=(
                    ("Paid","Paid"),
                    ("Partially Paid","PartiallyPaid"),
                    ("Unpaid","Unpaid")
    )
    status=models.CharField(max_length=15,choices=status_choices,default="Unpaid")
    due_date = models.DateField(blank = True,null = True)
    # Relationship Fields
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="sales"
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

    def update_status(self):
        print('updating invoice status')

    def save(self,*args,**kwargs):

        if self.term.due_days:
            self.due_date = self.created + timedelta(days=self.term.due_days)
        super(Invoice,self).save(*args,**kwargs)

class InvoiceItem(models.Model):

    # Fields
    quantity = models.IntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    less_stone = models.DecimalField(max_digits=10,decimal_places=3,default=0.0)
    touch = models.DecimalField(max_digits=10, decimal_places=3)
    wastage = models.DecimalField(max_digits=10,decimal_places=3,default=0.0)
    total = models.DecimalField(max_digits=10, decimal_places=3)
    is_return = models.BooleanField(default=False,verbose_name='Return')

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

    def get_charged_wt(self):
        pass


    def save(self,*args,**kwargs):

        print(f"In Sale Modelform save() :")
        print(f"item is_return: {self.is_return} ")
        print(self.product.refresh_from_db())

        sold,created = Stree.objects.get_or_create(name='Sold')
        if not self.is_return:#if sold
            if self.product.tracking_type =='Lot':
                # defrafmented tree logic
                sold_product,created = Stree.objects.get_or_create(name = self.product.name,
                                                            parent = sold,
                                                            barcode = self.product.barcode,
                                                            productvariant = self.product.productvariant
                                                            )
                try:
                    self.product.transfer(sold_product,self.quantity,self.weight)
                except Exception:
                    raise Exception("failed transfer")
                # end defragmentation logic
                # old logic
                # sold = sold.traverse_parellel_to(self.product)
                # print(f"moving { self.weight} from {self.product.get_family()[0].name} {self.product.weight} to {sold.get_family()[0].name}")
                # try:
                #     self.product.transfer(sold,self.quantity,self.weight)
                # except Exception:
                #     raise Exception("failed transfer")
                # print(f"moved from {self.product.get_family()[0]} {self.product.weight} to {sold.get_family()[0]}")
                # end old logic
            else:
                # defragmented tree logic
                # print("in else block saving unique node to sold")
                #
                self.product.move_to(sold,'first-child')
                self.product.update_status()
                # move_node(self.product,sold,position='last-child')

                # end defragmented tree logic
                # old logic
                # sold = sold.traverse_parellel_to(self.product,include_self=False)
                # print(f"moving { self.weight} from {self.product.get_family()[0]} {self.product.weight} to {sold.get_family()[0]} {sold.weight}")
                # self.product = self.product.move_to(sold,position='first-child')
                # old logic
        else:#if returned
            stock,created = Stree.objects.get_or_create(name='Stock')
            if self.product.tracking_type =='Lot':
                stock_product = Stree.object.create(name = self.product.name,
                                            barcode = self.barcode,parent = stock,
                                            productvariant = self.item.product.produtvariant
                                            )
                # stock = stock.traverse_parellel_to(self.product)
                print(f"moving { self.weight} from {self.product.get_family()[0]} {self.product.weight} to {stock.get_family()[0]} {stock.weight}")
                self.product.transfer(stock_product,self.quantity,self.weight)
                print(f"moved { self.weight} from {self.product.get_family()[0]} {self.product.weight} to {stock.get_family()[0]} {stock.weight}")
            else:
                # stock = stock.traverse_parellel_to(self.product,include_self=False)
                print(f"moving { self.weight} from {self.product.get_family()[0]} {self.product.weight} to {stock.get_family()[0]} {stock.weight}")
                self.product = self.product.move_to(stock,position='first-child')
        super(InvoiceItem,self).save(*args,**kwargs)
        self.invoice.update_status()
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
        on_delete=models.CASCADE, related_name="receipts"
    )

    class Meta:
        ordering = ('-created',)

    def update_status(self):
        total_allotted=self.get_line_totals()
        if total_allotted is not None :
            if total_allotted == self.total:
                self.status="Allotted"
            else:
                self.status="Unallotted"
        self.save()

    def deallot(self):
        self.receiptline_set.all().delete()

    def allot(self):
        print(f"allotting receipt {self.id} amount: {self.total}")

        invpaid = 0 if self.get_line_totals() is None else self.get_line_totals()
        print(f"invpaid{invpaid}")

        remaining_amount = self.total - invpaid
        print(f"amount : {remaining_amount}")

        try:
            invtopay = Invoice.objects.filter(customer=self.customer,balancetype=self.type).exclude(status="Paid").order_by('created')
        except IndexError:
            invtopay = None
        print(invtopay)

        for i in invtopay:
            print(f"i:{i} bal:{i.get_balance()}")
            if remaining_amount<=0 : break
            bal=i.get_balance()
            if remaining_amount >= bal :
                remaining_amount -= bal
                ReceiptLine.objects.create(receipt=self,invoice=i,amount=bal)
                i.status="Paid"
            else :
                ReceiptLine.objects.create(receipt=self,invoice=i,amount=remaining_amount)
                i.status="PartiallyPaid"
                remaining_amount=0
            i.save()
        print('allotted receipt')
        self.update_status()

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
