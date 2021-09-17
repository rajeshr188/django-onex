from approval.models import ApprovalLineReturn
from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse
from django.db import models,transaction
from contact.models import Customer
from product.models import Stock,StockTransaction
from django.utils import timezone
from django.db.models import Sum,Func,Q
from datetime import timedelta,date
from dea.models import Journal,JournalTypes
from invoice.models import PaymentTerm
from moneyed import Money
from django.utils.translation import gettext_lazy as _
class Month(Func):
    function = 'EXTRACT'
    template = '%(function)s(MONTH from %(expressions)s)'
    output_field = models.IntegerField()

class Year(Func):
    function = 'EXTRACT'
    template = '%(function)s(YEAR from %(expressions)s)'
    output_field = models.IntegerField()

class SalesQueryset(models.QuerySet):
    def posted(self):
        return self.filter(posted=True)

    def unposted(self):
        return self.filter(posted=False)

    def gst(self):
        return self.filter(is_gst=True)

    def non_gst(self):
        return self.filter(is_gst=False)

    def total(self):
        return self.aggregate(
            cash=Sum('balance', filter=Q(balancetype='INR')),
            gold=Sum('balance', filter=Q(balancetype='USD')),
            silver=Sum('balance', filter=Q(balancetype='AUD')),
        )

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

    def cur_month(self):
        return self.filter(created__month=date.today().month,
                           created__year=date.today().year)

class Invoice(models.Model):
    # Fields
    created = models.DateTimeField(default=timezone.now, db_index=True)
    last_updated = models.DateTimeField(auto_now_add=True)
    rate = models.DecimalField(max_digits=10, decimal_places=3,default=0)
    is_gst = models.BooleanField(default=False)
    posted = models.BooleanField(default=False)
    gross_wt = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    net_wt = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)
    discount = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    balance = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    class BType(models.TextChoices):
        CASH = 'INR', _("Cash"),
        GOLD = 'USD', _("Gold"),
        SILVER = 'AUD', _("Silver")
    metal_choices = (
        ("Gold","Gold"),
        ("Silver","Silver")
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
    is_active = models.BooleanField(default=True)
    objects = SalesQueryset.as_manager()

    # Relationship Fields
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="sales"
    )
    term = models.ForeignKey(
        PaymentTerm, on_delete=models.SET_NULL,
        null=True,
        related_name='sale_term',)
    approval = models.OneToOneField(
        'approval.Approval',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='bill'
    )
    journals = GenericRelation(Journal,related_query_name='sales_doc')
    stock_txns = GenericRelation(StockTransaction)

    class Meta:
        ordering = ('-created',)
        get_latest_by = ('id')

    def __str__(self):
        return f"{self.id}"

    def get_absolute_url(self):
        return reverse('sales_invoice_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('sales_invoice_update', args=(self.pk,))

    def get_next(self):
        return Invoice.objects.filter(id__gt=self.id).order_by('id').first()

    def get_previous(self):
        return Invoice.objects.filter(id__lt=self.id).order_by('id').last()

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
            return self.total - self.get_total_receipts()
        return self.total

    def save(self, *args, **kwargs):
        # if self.id and self.posted:
        #     raise Http404
        if self.total < 0:
            self.status = "Paid"
        self.due_date = self.created + timedelta(days=self.term.due_days)
        self.total = self.balance
        if self.is_gst:
            self.total += self.get_gst()
        
        super(Invoice, self).save(*args, **kwargs)
    
    def update_bal(self):
        self.gross_wt = self.get_gross_wt()
        self.net_wt = self.get_net_wt()
        self.save()
        
    def delete(self, *args, **kwargs):
        if self.approval:
            self.approval.is_billed = False
        super(Invoice, self).delete(*args, **kwargs)

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=['self.is_active'])

    def get_gst(self):
        if self.is_gst:
            return (self.balance * 3)/100
        return 0

    @transaction.atomic()
    def post(self):
        if not self.posted:
            if self.approval:
                for i in self.approval.items.filter(status = 'Pending'):
                    apr = ApprovalLineReturn.objects.create(
                        line=i, quantity=i.quantity, weight=i.weight)
                    apr.post()
                    i.update_status()
                self.approval.is_billed = True
                self.approval.save()
                self.approval.update_status()
            
            jrnl = Journal.objects.create(type = JournalTypes.SJ,
                    content_object = self, desc = 'sale')

            inv = "GST INV" if self.content_object.is_gst else "Non-GST INV"
            cogs = "GST COGS" if self.content_object.is_gst else "Non-GST COGS"
            money = Money(self.balance, self.btype)
            tax = Money(self.get_gst(), 'INR')
            lt = [{'ledgerno': 'sales', 'ledgerno_dr': 'Sundry Debtors', 'amount': money},
                  {'ledgerno': inv, 'ledgerno_dr': cogs, 'amount': money},
                  {'ledgerno': 'Output Igst', 'ledgerno_dr': 'Sundry Debtors', 'amount': tax}]
            at = [{'ledgerno': 'sales', 'xacttypecode': 'Cr', 'xacttypecode_ext': 'CRSL',
                   'account': self.customer.account, 'amount': money + tax}]
            jrnl.transact(lt,at)
            for i in self.saleitems.all():
                i.post(jrnl)
            self.posted = True
            self.save(update_fields = ['posted'])
        
    @transaction.atomic()   
    def unpost(self):
        if self.posted: 
            last_jrnl = self.journals.latest()
            if self.approval:
                self.approval.is_billed = False
                for i in self.approval.items.all():
                    i.unpost()
                    i.product.add(i.weight, i.quantity,i, 'A')
                    i.update_status()
                self.approval.save()
                self.approval.update_status()
                
            jrnl = Journal.objects.create(content_object=self,
                    desc='sale-revert')
            jrnl.untransact(last_jrnl)
            for i in self.saleitems.all():
                i.post(jrnl)
            self.posted = False
            self.save(update_fields = ['posted'])
  
class InvoiceItem(models.Model):
    # Fields
    huid = models.CharField(max_length=6, null=True, blank=True,unique = True)
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
        if self.invoice.customer.type == 'Re':
            return self.weight + self.wastage/100 
        else:
            return (self.weight * self.touch)/100

    def get_total(self):
        if self.invoice.balancetype == 'Cash':
            return self.get_nettwt() * self.invoice.rate
        else:
            return self.get_nettwt()

    def save(self,*args,**kwargs):
        super(InvoiceItem, self).save(*args, **kwargs)

    @transaction.atomic()   
    def post(self,jrnl):
        
        if not self.is_return:#if sold
            self.product.remove(self.weight,self.quantity,jrnl,'S')
        else:#if returned
            self.product.add(self.weight,self.quantity,jrnl,'SR')
    
    @transaction.atomic()
    def unpost(self,jrnl):
       
        if self.is_return:
            self.product.remove(self.weight,self.quantity,jrnl,'SR')
        else:   
            self.product.add(self.weight,self.quantity,jrnl,'SR')

class Receipt(models.Model):

    # Fields
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)

    class BType(models.TextChoices):
        CASH = 'INR', _("Cash"),
        GOLD = 'USD', _("Gold"),
        SILVER = 'AUD', _("Silver")
    type = models.CharField(max_length=30,verbose_name='Currency',
            choices=BType.choices,default= BType.CASH)
    rate= models.IntegerField(default=0)
    total = models.DecimalField(max_digits=10, decimal_places=3,default = 0)
    description = models.TextField(max_length=50,default="describe here")
    status_choices=(
                    ("Allotted","Allotted"),
                    ("Partially Allotted","PartiallyAllotted"),
                    ("Unallotted","Unallotted"))
    status=models.CharField(max_length=18,choices=status_choices,default="Unallotted")
    posted = models.BooleanField(default = False)
    is_active = models.BooleanField(default=True)
    journals = GenericRelation(Journal,related_query_name='receipt_doc')
    # Relationship Fields
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE, related_name="receipts")
    
    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return u'%s' % self.id

    def get_absolute_url(self):
        return reverse('sales_receipt_detail', args=(self.pk,))

    def get_update_url(self):
        return reverse('sales_receipt_update', args=(self.pk,))

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=['is_active'])

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
                            balancetype=self.type,posted = True
                            ).exclude(status="Paid").order_by('created')
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
        
        self.update_status()
    
    def post(self):
        if not self.posted:
            jrnl = Journal.objects.create(content_object = self,
                type = JournalTypes.RC, desc = 'Receipt')
            
            money = Money(self.total, self.type)
            lt = [{'ledgerno': 'Sundry Debtors', 'ledgerno_dr': 'Cash', 'amount': money}]
            at = [{'ledgerno': 'Sundry Debtors', 'xacttypecode': 'Dr', 'xacttypecode_ext': 'RCT',
                   'account': self.customer.account, 'amount': money}]
            jrnl.transact(lt,at)
            self.posted = True
            self.save(update_fields = ['posted'])

    def unpost(self):
        if self.posted:
            last_jrnl =- self.journals.latest()
            jrnl = Journal.objects.create(
                content_object=self,
                desc='Receipt-Revert')
            jrnl.untransact(last_jrnl)
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
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE)

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
