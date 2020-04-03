from django.db.models import signals
from django.dispatch import receiver
from purchase.models import Invoice,InvoiceItem,Payment,PaymentLine
from product.models import Stree

@receiver(signals.pre_delete,sender=PaymentLine)
def delete_status(sender,instance,*args,**kwargs):
    print ('deleting invoice status')
    inv=instance.invoice
    if inv.balance-instance.amount == 0:
        inv.status = "Unpaid"
    elif inv.balance-instance.amount > 0:
        inv.status = "PartiallyPaid"
    else :
        inv.status = "Error"
    inv.save()

@receiver(signals.post_delete,sender = InvoiceItem)
def remove_stock(sender,instance,*args,**kwargs):
    print('removing newly created stock')

    node = Stree.objects.get(name='Stock')
    node = node.traverse_to(instance.product)

    if instance.is_return:
        # remove from is return
        if node.tracking_type =='Lot':
            return_node = Stree.objects.get(name='Return')
            return_node = return_node.traverse_parellel_to(node)

            return_node.weight -= instance.weight
            return_node.quantity -= instance.quantity
            return_node.save()
            # add to stock
            node.weight +=instance.weight
            node.quantity +=instance.quantity
            node.save()
            print('Removed lot from Return and added to Stock')
        else:
            print("You need to merge stock to lot and return via purchase return.")

    else:
        # remove from stock
        if node.tracking_type =='Lot':
            node.weight -= instance.weight
            node.quantity -= instance.quantity
            node.save()
            node.update_status('Empty')
            print('Removed from Stock lot')
        else:
            node.delete()
            print('Deleted from stock unique')
