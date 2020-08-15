from django.db.models import signals
from django.dispatch import receiver
from .models import Approval,ApprovalLine,ApprovalLineReturn
from product.models import Stree


@receiver(signals.pre_delete,sender = ApprovalLine)
def submit_approval_stock(sender,instance,*args,**kwargs):
    print("In submit_approval_stock called after Delete of ApprovalLine")
    # print(f"before submitting {instance.product.id} :{instance.product.get_root().name}{instance.product}")
    if not instance.status == 'Returned':
        if instance.product.tracking_type == 'Lot':

            approval_node = Stree.objects.get(name='Approval')
            approval_node = approval_node.traverse_parellel_to(instance.product)
            approval_node.transfer(instance.product,instance.quantity,instance.weight)

        else:
            stock = Stree.objects.get(name='Stock')
            stock = stock.traverse_parellel_to(instance.product,include_self=False)
            instance.product.move_to(stock,position='first-child')
    # print(f"after submitting {instance.product.id}:{instance.product.get_root().name}{instance.product}")

@receiver(signals.pre_delete,sender = ApprovalLineReturn)
def not_returned(sender,instance,*args,**kwargs):
    print("In submit_approval_stock called after Delete of ApprovalREturnLine")
    if not instance.line.status == 'Returned':
        product = instance.line.product
        approval_node,created = Stree.objects.get_or_create(name='Approval')
        if product.tracking_type == 'Lot':
            approval_node = approval_node.traverse_parellel_to(product)
            product.transfer(approval_node,instance.quantity,instance.weight)
        else:
            approval_node = approval_node.traverse_parellel_to(product,include_self=False)
            product.move_to(approval_node,position='first-child')
        instance.line.returned_qty -=instance.quantity
        instance.line.returned_wt -=instance.weight
        if not instance.line.balance == 0:
            instance.line.status = "Pending"
        instance.line.save()
