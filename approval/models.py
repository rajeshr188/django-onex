from django.db import models
from contact.models import Customer
from product.models import Stree
from django.urls import reverse
# Create your models here.
class Approval(models.Model):

    created_at = models.DateTimeField(auto_now_add = True,editable = False)
    updated_at = models.DateTimeField(auto_now = True,editable = False)
    contact  = models.ForeignKey(Customer,related_name = 'contact',
                                on_delete = models.CASCADE)

    total_wt = models.DecimalField(max_digits=10,decimal_places=3,default =0)
    total_qty = models.IntegerField(default=0)
    status = models.CharField(max_length = 10,choices = (('Pending','Pending'),
                                ('Complete','Complete')),
                                default = 'Pending')

    class Meta:
        ordering = ('created_at',)

    def __str__(self):
        return f"{self.id}"

    def get_absolute_url(self):
        return reverse('approval_approval_detail',args=(self.pk,))

    def get_update_url(self):
        return reverse('approval_approval_update',args = (self.pk,))

    def update_status(self):
        pass

class ApprovalLine(models.Model):
    product = models.ForeignKey(Stree,related_name = 'product',
                                on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    weight = models.DecimalField(max_digits=10,decimal_places=3,default = 0.0)
    touch = models.DecimalField(max_digits=10,decimal_places=3,default = 0.0)
    returned_qty = models.IntegerField(default=0,blank = True)
    returned_wt = models.DecimalField(max_digits=10,decimal_places=3,default=0.0,blank = True)
    returned_on = models.DateTimeField(auto_now_add= True,blank = True)

    approval = models.ForeignKey(Approval,
                                on_delete = models.CASCADE)
    status = models.CharField(max_length =30, choices = (('Pending','Pending'),('Returned','Returned'),('Billed','Billed')), default = 'Pending',blank = True )

    class Meta:
        ordering = ('approval',)

    def balance(self):
        return self.weight - self.returned_wt

class ApprovalReturn(models.Model):

    created_at = models.DateTimeField(auto_now_add = True,editable = False)
    updated_at = models.DateTimeField(auto_now = True,editable = False)
    total_wt = models.DecimalField(max_digits=10,decimal_places=3,default =0)
    total_qty = models.IntegerField(default=0)
    approval = models.ForeignKey(Approval,
                                    on_delete = models.CASCADE)

    class Meta:
        ordering = ('created_at',)

    def __str__(self):
        return self.id

    def get_absolute_url(self):
        return reverse('approval_approvalreturn_detail',args=(self.pk,))


class ApprovalReturnLine(models.Model):
    product = models.ForeignKey(Stree,
                                on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    weight = models.DecimalField(max_digits=10,decimal_places=3,default = 0.0)

    approvalreturn = models.ForeignKey(ApprovalReturn,
                                on_delete = models.CASCADE)

    class Meta:
        ordering = ('approvalreturn',)

    def __str__(self):
        return self.id
