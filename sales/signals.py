from django.db.models import signals
from django.dispatch import receiver
from sales.models import ReceiptLine

# @receiver(signals.pre_delete,sender=ReceiptLine)
# def delete_status(sender,instance,*args,**kwargs):
#     print ('deleting invoice status')
#     inv=instance.invoice
#     if inv.balance-instance.amount == 0 :
#         inv.status = "Unpaid"
#     elif inv.balance-instance.amount > 0:
#         inv.status = "PartiallyPaid"
#     else :
#         inv.status = "Error"
#     inv.save()
#     print('updating receipt Amount')
#     rec = instance.receipt
#     rec.total -= instance.amount
#     rec.save()

@receiver(signals.post_delete,sender=ReceiptLine)
def delete_status(sender,instance,*args,**kwargs):
    print ('deleting invoice status')
    inv=instance.invoice
    print(f"in bal :{inv.get_balance()}")
    if inv.get_balance() == inv.balance:
        inv.status = "Unpaid"
    else :
        inv.status = "PartialPaid"
    inv.save()
    # print('updating receipt Amount')
    # rec = instance.receipt
    # rec.total -= instance.amount
    # rec.save()

    # these following lines must go since these eat up receipt amount on delete
    # a=instance.receipt.total-instance.amount
    # Receipt.objects.filter(id=instance.receipt.id).update(total=a)

# decoupling receipt allotment
# @receiver(signals.post_save,sender=Receipt)
# def allot_receipt(sender,instance=None,created=False,*args,**kwargs):
#
#     if not instance:
#         return
#
#     if hasattr(instance, '_dirty'):
#         return
#
#     print(f"allotting receipt {instance.id} amount: {instance.total}")
#     amount=instance.total
#     invpaid = 0 if instance.get_line_totals() is None else instance.get_line_totals()
#     print(f"invpaid{invpaid}")
#     amount = amount - invpaid
#     print(f"amount : {amount}")
#     try:
#         invtopay = Invoice.objects.filter(customer=instance.customer,balancetype=instance.type).exclude(status="Paid").order_by('created')
#     except IndexError:
#         invtopay = None
#     print(invtopay)
#     for i in invtopay:
#         print(f"i:{i} bal:{i.get_balance()}")
#         if amount<=0 : break
#         bal=i.get_balance()
#         if amount >= bal :
#             amount -= bal
#             ReceiptLine.objects.create(receipt=instance,invoice=i,amount=bal)
#             i.status="Paid"
#         else :
#             ReceiptLine.objects.create(receipt=instance,invoice=i,amount=amount)
#             i.status="PartiallyPaid"
#             amount=0
#         i.save()
#     print('allotted receipt')
#     try:
#         instance._dirty = True
#         instance.save()
#     finally:
#         del instance._dirty

# @receiver(signals.pre_delete,sender = InvoiceItem)
# def submit_stock(sender,instance,*args,**kwargs):
#     if instance.invoice.posted:
#         instance.unpost()
