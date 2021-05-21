from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse
from django.db import models,transaction
from contact.models import Customer
from product.models import Stock,StockTransaction
from django.utils import timezone
from django.db.models import Sum,Func
from datetime import timedelta
from dea.models import Journal,SalesJournal,ReceiptJournal,LedgerStatement
from invoice.models import PaymentTerm
# from django.contrib.postgres.indexes import BrinIndex


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
    ptype_choices = (
        ("Cash", "Cash"),
        ("Credit", "Credit")
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
    paymenttype = models.CharField(
        max_length=30, choices=ptype_choices, default="Credit")

    due_date = models.DateField(null=True, blank=True)

    # Relationship Fields
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="sales"
    )
    term = models.ForeignKey(
        PaymentTerm, on_delete=models.SET_NULL,
        related_name='sale_term',
        blank=True, null=True)
    journals = GenericRelation(Journal,related_query_name='sales_doc')
    stock_txns = GenericRelation(StockTransaction)

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
    
    def get_gross_wt(self):
        return self.saleitems.aggregate(t=Sum('weight'))['t']

    def get_net_wt(self):
        return self.saleitems.aggregate(t=Sum('net_wt'))['t']
    
    def get_total_balance(self):
        return self.saleitems.aggregate(t= Sum('total'))['t']

    def get_total_receipts(self):
        paid=self.receiptline_set.aggregate(t=Sum('amount'))
        return paid['t']

    @property
    def overdue_days(self):
        return (timezone.now().date() - self.date_due).days

    def get_balance(self):
        if self.get_total_receipts() != None :
            return self.balance - self.get_total_receipts()
        return self.balance

    def save(self, *args, **kwargs):
        # if self.id and self.posted:
        #     raise Http404
        if self.term.due_days:
            self.due_date = self.created + timedelta(days=self.term.due_days)
        if self.is_gst:
            self.total = self.balance
            self.total += self.get_gst()
        super(Invoice, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.posted and self.get_balance() != 0:
            raise Exception("Cant delete sale if posted")
        else:
            super(Invoice, self).delete(*args, **kwargs)

    def get_gst(self):
        if self.invoicetype == 'GST':
            return (self.balance * 3)/100
        return 0

    @transaction.atomic()
    def post(self):
        try:
            ls = LedgerStatement.objects.latest().first().created
        except LedgerStatement.DoesNotExist:
            ls = None
        if ls is None or self.created >= ls.created:
            saleitems = self.saleitems.all()
            
            for i in saleitems:
                i.post()
            jrnl = SalesJournal.objects.create(
                content_object = self,
                desc = 'sale'
            )
            # credit/cash cash/gold
            
            jrnl.transact()
            self.posted = True
            self.save(update_fields = ['posted'])
        else:
            raise ValueError("cant post sale created before latest audit")

    @transaction.atomic()   
    def unpost(self):
        try:
            ls = LedgerStatement.objects.latest()
        except LedgerStatement.DoesNotExist:
            ls = None
        if ls is None or ls.created < self.created:
            for i in self.saleitems.all():
                i.unpost()
            self.journals.clear()
            self.posted = False
            self.save(update_fields = ['posted'])
        else:
            raise ValueError("cant unpost sale created before latest audit")

    
class InvoiceItem(models.Model):
    # Fields
    quantity = models.IntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    # remove less stone
    less_stone = models.DecimalField(max_digits=10,decimal_places=3,default =0)
    touch = models.DecimalField(max_digits=10, decimal_places=3)
    wastage = models.DecimalField(max_digits=10,decimal_places=3,default =0)
    net_wt = models.DecimalField(max_digits=10,decimal_places=3,default=0)
    total = models.DecimalField(max_digits=10, decimal_places=3)
    is_return = models.BooleanField(default=False,verbose_name='Return')
    makingcharge=models.DecimalField(max_digits=10,decimal_places=3,default =0)
    # Relationship Fields
    product = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name="products"
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

    
    def post(self):
        if not self.is_return:#if sold
            self.product.remove(self.weight,self.quantity,self.invoice,'S')
        else:#if returned
            self.product.add(self.weight,self.quantity,self.invoice,'SR')
    
    @transaction.atomic()
    def unpost(self):
        if self.is_return:
            self.product.remove(self.weight,self.quantity,self.invoice,'SR')
        else:
            self.product.add(self.weight,self.quantity,self.invoice,'SR')

class Receipt(models.Model):

    # Fields
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)
    btype_choices=(
                ("Cash","Cash"),
                ("Gold", "Gold"),
                ("silver", "Silver")
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
    posted = models.BooleanField(default = False)
    journals = GenericRelation(Journal,related_query_name='receipt_doc')
    # Relationship Fields
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE, related_name="receipts"
    )
    
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
    
    def post(self):
        jrnl = ReceiptJournal.objects.create(
            content_object = self,
            desc = 'Receipt'
            )
        jrnl.transact()
        self.posted = True
        self.save(update_fields = ['posted'])
    def unpost(self):
        self.journals.clear()
        self.posted = False
        self.save(update_fields = ['posted'])

class ReceiptItem(models.Model):
    weight = models.DecimalField(
        max_digits=10, blank=True, decimal_places=3, default=0.0)
    touch = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, default=0.0)
    nettwt = models.DecimalField(
        max_digits=10, blank=True, decimal_places=3, default=0.0)
    rate = models.IntegerField(default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=3)
    payment = models.ForeignKey(Receipt, on_delete=models.CASCADE)

    def __str__(self):
        return self.amount

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
