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
    stock = instance.product
    weight = instance.weight
    print(f"item.weight : {instance.weight}")

    node = Stree.objects.get(name='Gold')
    node = node.traverse_to(stock)
    print(f"reached node{node}")

    if node.tracking_type == 'Lot':
        if instance.is_return:
            print(f"is_return:{instance.is_return}")
            node.weight -= weight
        else:
            node.weight += weight
        node.save()
        print(f"stock is lot so updating weight of {node.get_ancestors()}{node.weight}")
    else :
        if not instance.is_return:
            print(f"stock is unique so deleting {stock}")
            print(node.get_children())
            print(weight)
            node = Stree.objects.get(parent = node,weight = instance.weight)
            print(f"deleting node:{node} of family{node.get_ancestors()}")
            node.delete()
        else:
            # unique product which is to be returned cannot be created again when puchase is delted
            print("You need to merge stock to lot and return via purchase return.")
