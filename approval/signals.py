from django.db.models import signals
from django.dispatch import receiver
from .models import Approval,ApprovalLine
from product.models import Stree


@receiver(signals.pre_delete,sender = ApprovalLine)
def submit_approval_stock(sender,instance,*args,**kwargs):
    print("In submit_approval_stock called after Delete of ApprovalLine")
    print(f"before submitting {instance.product.id} :{instance.product.get_root().name}{instance.product}")
    if instance.product.tracking_type == 'Lot':

        approval_node = Stree.objects.get(name='Approval')
        approval_node = approval_node.traverse_parellel_to(instance.product)
        approval_node.transfer(instance.product,instance.quantity,instance.weight)

    else:
        stock = Stree.objects.get(name='Stock')
        stock = stock.traverse_parellel_to(instance.product,include_self=False)
        instance.product.move_to(stock,position='first-child')
    print(f"after submitting {instance.product.id}:{instance.product.get_root().name}{instance.product}")
