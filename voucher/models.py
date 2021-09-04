from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.fields.related import ForeignKey

# Create your models here.
class VoucherType(models.Model):
    pass

class Voucher(models.Model):
    voucher_type = models.ForeignKey(VoucherType)
    created = models.DateTimeField()
    modified = models.DateTimeField()
    voucher_no = models.CharField()
    account = models.ForeignKey()
    from_ledger = models.ForeignKey()
    to_ledger = ForeignKey()
    amount = models.DecimalField()
    is_posted = models.BooleanField()

class Transaction(models.Model):
    voucher = models.ForeignKey(Voucher)
    created = models.DateTimeField()
    ledger = models.ForeignKey()
    amount = models.DecimalField()

class LedgerTransaction(models.Model):
    ledgerno_dr = models.ForeignKey()

class AccountTransaction(models.Model):
    pass
    # XactTypeCode = models.ForeignKey(TransactionType_DE,
    #                 on_delete = models.CASCADE)
    # XactTypeCode_ext = models.ForeignKey(TransactionType_Ext,
    #                     on_delete=models.CASCADE)
    # Account = models.ForeignKey(Account,on_delete=models.CASCADE,
    #                         related_name='accounttransactions')

class InventoryTransaction(models.Model):
    ledgerno_dr = models.ForeignKey()

class salesVoucher(Voucher):
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

class PurchaseVoucher(Voucher):
    acc = models.ForeignKey()
    invoice_no = models.IntegerField()
    gross_wt = models.DecimalField()
    net_wt = models.DecimalField()
    rate = models.DecimalField()
    total = models.DecimalField()
    is_gst = models.BooleanField()
    status = models.CharField()

class ReceiptVoucher(Voucher):
    acc =models.ForeignKey()

class PaymentVoucher(Voucher):
    acc = models.ForeignKey()




