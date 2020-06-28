from django.db import models

# Create your models here.
class Book(models.Model):
    name = models.CharField(unique=True)
    opening_date = models.DateField()
    closing_date = models.DateField()
    opening_bal = models.IntegerField()
    closing_bal = models.IntegerField()
    is_balanced = models.BooleanField(default = True)

    def __str__(self):
        return self.name

class Page(models.Model):
    date =models.DateField(auto_now_add = True,primary_key = True)

    def __str__(self):
        return self.id

class Account(models.Model):
    name = models.CharField(max_length = 30)
    acc_type = models.CharField(choices=(('Jama','Jama'),('Nave','Nave')),default='Jama')
    balance = models.IntegerField()
    page = models.ForeignKey(Page,on_delete = models.CASCADE)
