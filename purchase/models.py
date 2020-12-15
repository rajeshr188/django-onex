from django.urls import reverse
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth import models as auth_models
from django.db import models
from contact.models import Customer
from product.models import ProductVariant
from django.utils import timezone
from django.db.models import Avg,Count,Sum

from django.contrib.contenttypes.fields import GenericRelation
from product.models import Stock,StockTransaction

class Invoice(models.Model):

    # Fields
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now_add=True)
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
                    ("PartiallyPaid","PartiallyPaid"),
                    ("Unpaid","Unpaid")
    )
    status=models.CharField(max_length=15,choices=status_choices,default="Unpaid")

    # Relationship Fields
    supplier = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE, related_name="purchases"
    )
    posted = models.BooleanField(default = False)
    # txns = GenericRelation(StockTransaction)

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

    def delete(self, *args, **kwargs):
        if not self.posted:
            super(Invoice, self).delete(*args, **kwargs)

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

    def post(self):
        if not self.is_return:
            if 'Lot' in self.product.name:
                stock,created = Stock.objects.get_or_create(variant = self.product,
                                                    tracking_type = 'Lot',
                                                    )
                if created:
                    stock.barcode='je'+ str(stock.id)
                    stock.save()
                print(type(stock.weight))
                print(type(self.weight))
                stock.add(self.weight,self.quantity,
                            self.weight,self.quantity,
                            self.invoice,'P')
            else:
                stock = Stock.objects.create(variant = self.product,
                                            tracking_type = 'Unique')

                stock.barcode='je'+ str(stock.id)
                stock.add(self.weight,self.quantity,
                            self.weight,self.quantity,
                            self.invoice,'P')

        else:
            # is return true
            if 'Lot' in self.product.name:
                stock = Stock.get(name = self.product.name)
                stock.remove(self.weight,self.quantity,
                                self.weight,self.quantity,
                                self.invoice,'PR')
            else:
                print("merge unique to lot before returning")

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
                self.weight,self.quantity,
                cto = self.invoice,
                at = 'PR'
                )


    # def save(self,*args,**kwargs):
    #     print("In purchase line item model save()")
        # if not self.is_return:
        #     if 'Lot' in self.product.name:
        #         stock,created = Stock.objects.get_or_create(variant = self.product,
        #                                             tracking_type = 'Lot',
        #                                             )
        #         if created:
        #             stock.barcode='je'+ str(stock.id)
        #             stock.save()
        #         print(type(stock.weight))
        #         print(type(self.weight))
        #         stock.add(self.weight,self.quantity,
        #                     self.weight,self.quantity,
        #                     self.invoice,'P')
        #     else:
        #         stock = Stock.objects.create(variant = self.product,
        #                                     tracking_type = 'Unique')
        #
        #         stock.barcode='je'+ str(stock.id)
        #         stock.add(self.weight,self.quantity,
        #                     self.weight,self.quantity,
        #                     self.invoice,'P')
        #
        # else:
        #     # is return true
        #     if 'Lot' in self.product.name:
        #         stock = Stock.get(name = self.product.name)
        #         stock.remove(self.weight,self.quantity,
        #                         self.weight,self.quantity,
        #                         self.invoice,'PR')
        #     else:
        #         print("merge unique to lot before returning")
        # super(InvoiceItem,self).save(*args,**kwargs)
        # print("actually saving purchase line item")

class Payment(models.Model):

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
    description = models.TextField(max_length=100)
    status_choices = (
                        ("Allotted","Allotted"),
                        ("Partially Allotted","PartiallyAllotted"),
                        ("Unallotted","Unallotted"),
                        )
    status=models.CharField(max_length=18,choices=status_choices,default="Unallotted")

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
