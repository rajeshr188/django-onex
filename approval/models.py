from django.db import models,transaction
from contact.models import Customer
from product.models import Stock
from django.urls import reverse
from django.db.models import Sum
# Create your models here.
class Approval(models.Model):

    created_at = models.DateTimeField(auto_now_add = True,
                editable = False)
    updated_at = models.DateTimeField(auto_now = True,
                editable = False)
    contact  = models.ForeignKey(Customer,
                related_name = 'contact',on_delete = models.CASCADE)
    total_wt = models.DecimalField(max_digits=10,
                decimal_places=3,default =0)
    total_qty = models.IntegerField(default=0)
    posted = models.BooleanField(default = False)
    is_billed = models.BooleanField(default = False)
    status = models.CharField(max_length = 10,
            choices = (('Pending','Pending'),
                ('Complete','Complete')),default = 'Pending')

    class Meta:
        ordering = ('created_at',)

    def __str__(self):
        return f"{self.id}"

    def get_absolute_url(self):
        return reverse('approval_approval_detail',args=(self.pk,))

    def get_update_url(self):
        return reverse('approval_approval_update',args = (self.pk,))

    @transaction.atomic()
    def post(self):
        if not self.posted:
            for i in self.items.all():
                i.post()
        self.posted = True
        self.save(update_fields=['posted'])

    @transaction.atomic()
    def unpost(self):
        # if is billed cant unpost
        if self.posted and not self.is_billed:
            for i in self.items.all():
                i.unpost()
            self.posted = False
            self.save(update_fields=['posted'])

    def update_status(self):
        print('in approval update_Status')
        for i in self.items.all():
            print(f"{i}-{i.status} ")
        if any(i.status == 'Pending' for i in self.items.all()):
            self.status ='Pending'
        else:
            self.status ='Complete'
        self.save()
       
class ApprovalLine(models.Model):
    product = models.ForeignKey(Stock,related_name = 'product',
                    on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    weight = models.DecimalField(max_digits=10,
                    decimal_places=3,default = 0.0)
    touch = models.DecimalField(max_digits=10,
                    decimal_places=3,default = 0.0)

    approval = models.ForeignKey(Approval,
                    on_delete = models.CASCADE,
                    related_name='items')
    
    status = models.CharField(max_length =30,
                    choices = (
                        ('Pending','Pending'),
                        ('Returned','Returned'),
                        ('Billed','Billed')),
                        default = 'Pending',
                        blank = True )

    class Meta:
        ordering = ('approval',)

    def __str__(self):
        return f"{self.id}"

    def balance(self):
        return (self.weight - self.approvallinereturn_set.filter(posted = True).\
            aggregate(t = Sum('weight'))['t'])

    def post(self):
        self.product.remove(self.weight,self.quantity,None,'A')

    def unpost(self):
        for i in self.approvallinereturn_set.all():
            i.unpost()
            i.delete()
        self.product.add(self.weight, self.quantity, None, 'AR')

    def update_status(self):
        ret = self.approvallinereturn_set.filter(
                    posted = True
                    ).aggregate(
                        qty = Sum('quantity'),
                        wt = Sum('weight'))
        if self.quantity == ret['qty'] and self.weight == ret['wt']:
            self.status = 'Returned'
        else:
            self.status = 'Pending'
        self.save()
        self.approval.update_status()


class ApprovalLineReturn(models.Model):
    created_at = models.DateTimeField(auto_now_add = True)
    line = models.ForeignKey(ApprovalLine,on_delete = models.CASCADE)
    quantity = models.IntegerField(default = 0)
    weight = models.DecimalField(max_digits = 10,
                    decimal_places = 3,default =0.0)
    posted = models.BooleanField(default=False)

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return f"{self.line.product}"

    def post(self):
        if not self.posted:
            self.line.product.add(self.weight, self.quantity, None, 'AR')
            self.posted = True
            self.save(update_fields=['posted'])
            self.line.update_status()
    def unpost(self):
        if self.posted:
            self.line.product.remove(self.weight, self.quantity, None, 'A')
            self.posted = False
            self.save(update_fields=['posted'])
            self.line.update_status()