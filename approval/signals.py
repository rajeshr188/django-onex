from django.db.models import signals
from django.dispatch import receiver
from .models import Approval,ApprovalLine
from product.models import Stree


@receiver(signals.post_delete,sender = ApprovalLine)
def submit_approval_stock(sender,instance,*args,**kwargs):
    print("In submit_approval_stock called after Delete of ApprovalLine")
    if instance.product.tracking_type == 'Lot':
        instance.product.weight += instance.weight
        instance.product.quantity +=instance.quantity
        instance.product.save()
        instance.product.update_status()

        approval_node = Stree.objects.get(name='Approval')
        approval_node = approval_node.traverse_parellel_to(instance.product)
        approval_node.weight -= instance.weight
        approval_node.quantity -= instance.quantity
        approval_node.save()

    else:
        stock = Stree.objects.get(name='Stock')
        stock = stock.traverse_parellel_to(instance.product,include_self=False)
        instance.product.move_to(stock,position='first-child')
