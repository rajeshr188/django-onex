from django.db import models
from mptt.models import MPTTModel,TreeeForeignKey
# Create your models here.
class Account(models.Model):
    name = CharField(max_length=30,unique =True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class MPTTMeta:
        order_insertion_by = ['name']

class Transaction(models.Model):

    account = models.ForeignKey('Account',on_delete = models.CASCADE)
    txn_type = models.CharField(choices = {{"CREDIT","CREDIT"},("DEBIT","DEBIT")},default ="CREDIT")
    amount = models.DecimalField(decimal_places=2,max_digits=10)

class Book(models.Model):
    date = models.DateField(unique = True)
    op_bal = models.DecimalField(decimal_places=3,max_digits=8)
    cl_bal = models.DecimalField(decimal_places=3,max_digits=8)
