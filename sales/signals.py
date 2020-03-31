from django.db.models import signals
from django.dispatch import receiver
from sales.models import Invoice,InvoiceItem,Receipt,ReceiptLine

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
@receiver(signals.post_delete,sender = InvoiceItem)
def submit_stock(sender,instance,*args,**kwargs):

    node = instance.product

    weight = instance.weight
    print(f"item.product:{node} weight : {weight}")
    if instance.is_return:
        node.weight -=weight
    else :
        node.weight += weight
    print(f"after submitting stock node weight :{node.weight}")
    node.save()
@receiver(signals.post_delete,sender=ReceiptLine)
def delete_status(sender,instance,*args,**kwargs):
    # print ('deleting invoice status')
    inv=instance.invoice
    if inv.get_balance() == inv.balance:
        inv.status = "Unpaid"
    else :
        inv.status = "PartialPaid"
    inv.save()
    # print('updating receipt Amount')
    # rec = instance.receipt
    # rec.total -= instance.amount
    # rec.save()
    a=instance.receipt.total-instance.amount
    Receipt.objects.filter(id=instance.receipt.id).update(total=a)

@receiver(signals.post_save,sender=Receipt)
def allot_receipt(sender,instance=None,created=False,*args,**kwargs):

    if not instance:
        return

    if hasattr(instance, '_dirty'):
        return

    # print('allotting receipt'+instance.id)
    amount=instance.total
    invpaid = 0 if instance.get_line_totals() is None else instance.get_line_totals()
    amount = amount - invpaid

    try:
        invtopay = Invoice.objects.filter(customer=instance.customer,balancetype=instance.type).exclude(status="Paid").order_by('created')
    except IndexError:
        invtopay = None
    # print(invtopay)
    for i in invtopay:
        # print(i)
        if amount<=0 : break
        bal=i.get_balance()
        if amount >= bal :
            amount -= bal
            ReceiptLine.objects.create(receipt=instance,invoice=i,amount=bal)
            i.status="Paid"
        else :
            ReceiptLine.objects.create(receipt=instance,invoice=i,amount=amount)
            i.status="PartiallyPaid"
            amount=0
        i.save()
    # print('allotted receipt')
    try:
        instance._dirty = True
        instance.save()
    finally:
        del instance._dirty
