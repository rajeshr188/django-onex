from django.db.models import signals
from django.dispatch import receiver
from sales.models import Invoice,InvoiceItem,Receipt,ReceiptLine
from product.models import Stree

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
    a=instance.receipt.total-instance.amount
    Receipt.objects.filter(id=instance.receipt.id).update(total=a)

@receiver(signals.post_save,sender=Receipt)
def allot_receipt(sender,instance=None,created=False,*args,**kwargs):

    if not instance:
        return

    if hasattr(instance, '_dirty'):
        return

    print(f"allotting receipt {instance.id} amount: {instance.total}")
    amount=instance.total
    invpaid = 0 if instance.get_line_totals() is None else instance.get_line_totals()
    print(f"invpaid{invpaid}")
    amount = amount - invpaid
    print(f"amount : {amount}")
    try:
        invtopay = Invoice.objects.filter(customer=instance.customer,balancetype=instance.type).exclude(status="Paid").order_by('created')
    except IndexError:
        invtopay = None
    print(invtopay)
    for i in invtopay:
        print(f"i:{i} bal:{i.get_balance()}")
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
    print('allotted receipt')
    try:
        instance._dirty = True
        instance.save()
    finally:
        del instance._dirty

@receiver(signals.post_delete,sender = InvoiceItem)
def submit_stock(sender,instance,*args,**kwargs):

    if instance.is_return:
        if instance.product.tracking_type =='Lot':
            # remove from stock
            instance.product.weight -= instance.weight
            instance.product.quantity -=instance.quantity
            instance.product.save()
            # add to sold
            sold = Stree.objects.get(name='Sold')
            sold = sold.traverse_parellel_to(instance.product)
            sold.weight +=instance.weight
            sold.quantity +=instance.quantity
            sold.save()
        else:
            # move unique back to sold
            sold = Stree.objects.get(name='Sold')
            instance.product.move_to(sold)


    else:
        if instance.product.tracking_type =='Lot':
            # remove from sold
            sold = Stree.objects.get(name='Sold')
            sold = sold.traverse_parellel_to(instance.product)
            sold.weight -=instance.weight
            sold.quantity -=instance.quantity
            sold.save()
            # add to stock
            instance.product.weight +=instance.weight
            instance.product.quantity +=instance.quantity
            instance.product.save()

        else:
            # move unique back to stock
            stock = Stree.objects.get(name='Stock')
            stock = stock.traverse_parellel_to(instance.product)
            instance.product.move_to(stock)


    # 1
    # node = instance.product
    # weight = instance.weight
    # quantity = instance.quantity
    # print(f"Submitting item.product:{node.get_family()} weight : {node.weight}")
    #
    #
    # if node.tracking_type=='Lot':
    #     sold = Stree.objects.get(name='Sold')
    #     sold = sold.traverse_parellel_to(node)
    #     print(f"traversed to Sold Node : {sold.get_family()} wt = {sold.weight}")
    #     node.weight += weight
    #     node.quantity += quantity
    #     node.save()
    #     print(f"item.product:{node} weight : {node.weight}")
    #     sold.weight -=weight
    #     sold.quantity -= quantity
    #     sold.save()
    # else:
    #     stock = Stree.objects.get(name='Stock')
    #     stock = stock.traverse_parellel_to(node)
    #     print(f"traversed to stock Node : {stock.get_family()} wt = {stock.weight}")
    #     node.move_to(stock,position='left')
    #     node.save()


    # 0
    # if instance.is_return:
    #     node.weight -=weight
    #     node.quantity -=quantity
    # else :
    #     node.weight += weight
    #     node.quantity +=instance.quantity
    # print(f"after submitting stock node weight :{node.weight}")
    # node.save()
