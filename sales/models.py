from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse
from django.db import models
from contact.models import Customer
from product.models import Stock
from django.utils import timezone
from django.db.models import Sum,Func
from datetime import timedelta
from dea.models import Journal,SalesJournal
# from django.contrib.postgres.indexes import BrinIndex


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
            ("Gold","Gold"),
            ("Silver","Silver"),
        )
    itype_choices=(
        ("Cash","Cash"),
        ("Credit","Credit")
    )
    balancetype = models.CharField(max_length=30,choices=btype_choices,default="Cash")
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
    posted = models.BooleanField(default = False)
    journals = GenericRelation(Journal)

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

    def post(self):
        jrnl = SalesJournal.objects.create(
            content_type = self,
            type = Journal.Types.SJ,
            desc = 'sale'
        )
        # credit/cash cash/gold
        jrnl.sale(self,self.customer.account,self.balance,
                    self.paymenttype,self.balancetype)
        self.posted = True
        self.save(update_fields = ['posted'])
        
    def unpost(self):
        self.journals.clear()
        self.posted = False
        self.save(update_fields = ['posted'])

    def save(self,*args,**kwargs):
        if self.term.due_days:
            self.due_date = self.created + timedelta(days=self.term.due_days)
        super(Invoice,self).save(*args,**kwargs)

    def delete(self, *args, **kwargs):
        if not self.posted:
            super(Invoice, self).delete(*args, **kwargs)
        else:
            raise Exception("Cant delete sale if posted")

class InvoiceItem(models.Model):
    # Fields
    quantity = models.IntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    # remove less stone
    less_stone = models.DecimalField(max_digits=10,decimal_places=3)
    touch = models.DecimalField(max_digits=10, decimal_places=3)
    wastage = models.DecimalField(max_digits=10,decimal_places=3)
    total = models.DecimalField(max_digits=10, decimal_places=3)
    is_return = models.BooleanField(default=False,verbose_name='Return')
    makingcharge=models.DecimalField(max_digits=10,decimal_places=3)
    # Relationship Fields
    product = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE
    )
    invoice = models.ForeignKey(
        'sales.Invoice',
        on_delete=models.CASCADE,
        related_name="saleitems"
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

    def post(self):
        if not self.is_return:#if sold
            self.product.remove(0,0,self.weight,self.quantity,self.invoice,'S')
        else:#if returned
            self.product.add(0,0,self.weight,self.quantity,self.invoice,'SR')
    def unpost(self):
        if self.is_return:
            self.product.remove(0,0,self.weight,self.quantity,self.invoice,'SR')
        else:
            self.product.add(0,0,self.weight,self.quantity,self.invoice,'SR')

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
    posted = models.BooleanField(default = False)
    journal = GenericRelation(Journal)
    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return u'%s' % self.id

    def get_absolute_url(self):
        return reverse('sales_receipt_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('sales_receipt_update', args=(self.pk,))

    def get_line_totals(self):
        return self.receiptline_set.aggregate(t=Sum('amount'))['t']

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
        self.update_status()

    def allot(self):
        print(f"allotting receipt {self.id} amount: {self.total}")

        invpaid = 0 if self.get_line_totals() is None else self.get_line_totals()

        remaining_amount = self.total - invpaid

        try:
            invtopay = Invoice.objects.filter(customer=self.customer,
                                        balancetype=self.type,
                                        posted = True).exclude(
                                        status="Paid").order_by('created')
        except IndexError:
            invtopay = None

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

    def save(self,*args,**kwargs):
        if self.id:
            self.deallot()
        super(self,Receipt).save(*args,**kwargs)
        self.allot()
    
    def post(self):
        pass
    def unpost(self):
        pass

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
