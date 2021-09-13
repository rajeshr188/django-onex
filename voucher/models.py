from product.models import StockTransaction
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.fields.related import ForeignKey

# Create your models here.
class VoucherType(models.Model):
    name = models.CharField()

class Voucher(models.Model):
    voucher_type = models.ForeignKey(VoucherType)
    created = models.DateTimeField()
    modified = models.DateTimeField()
    voucher_no = models.CharField()
    amount = models.DecimalField()
    posted = models.BooleanField()

    def transact(self,revert = False):
        # do self.ledgertransactions
        # do self.acc tranxn
        # do self.stock trxn
        return NotImplementedError



class InvoiceVoucher(Voucher):
    # l - l trnsaction# from_ledger isinventory to ledger is sales
    # l-a trsxn from inventory to acc
    #  if is gst add another l-l txns cr from taxliabnility debit to sundryt debtor
    acc = models.ForeignKey()
    gross_wt = models.DecimalField()
    net_wt = models.DecimalField()
    rate = models.DecimalField()
    total = models.DecimalField()
    is_gst = models.BooleanField()
    status = models.CharField()

class PaymentVoucher(Voucher):
    acc = models.ForeignKey()
    invoice_no = models.IntegerField()
    gross_wt = models.DecimalField()
    net_wt = models.DecimalField()
    rate = models.DecimalField()
    total = models.DecimalField()
    is_gst = models.BooleanField()
    status = models.CharField()

    def post(self):
        # LedgerTransaction.objects.create_txn()
        # LedgerTransaction.objects.create_txn()
        # AccountTransaction.objects.create_Txn()
        for i in self.items:
            i.post()

        self.posted = True

    def unpost(self):
        # LedgerTransaction.objects.create_txn()
        # LedgerTransaction.objects.create_txn()
        # AccountTransaction.objects.create_Txn()
        for i in self.items:
            i.unpost()

        self.posted = False



