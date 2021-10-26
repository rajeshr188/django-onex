from django.contrib.contenttypes.models import ContentType
from django.db import models

# Create your models here.
class Voucher(models.Model):
    
    created = models.DateTimeField()
    modified = models.DateTimeField()
    amount = models.DecimalField()
    posted = models.BooleanField()
    status = models.CharField()

    def get_lt(self):
        return []
    
    def get_at(self):
        return []

    def get_st(self):
        return []

    def post():
        return 
    
    def unpost():
        return


class InvoiceVoucher(Voucher):
    # l - l trnsaction# from_ledger isinventory to ledger is sales
    # l-a trsxn from inventory to acc
    #  if is gst add another l-l txns cr from taxliabnility debit to sundryt debtor
    acc = models.ForeignKey()
    
    rate = models.DecimalField()
    total = models.DecimalField()
    is_gst = models.BooleanField()
    balance = models.DecimalField()
    

class PaymentVoucher(Voucher):
    acc = models.ForeignKey()
    invoice_no = models.IntegerField()  
    rate = models.DecimalField()
    total = models.DecimalField()

    def post(self):
        # create a journal
        # get at,lt,st as list and pass it to journal.trnasact

        self.posted = True

    def unpost(self):
        
        # get last jrnl
        # create new jrnl and pass last jrnl as jrnl.untransact(last_jrnl)

        self.posted = False



