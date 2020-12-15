from django.db.models import signals
from django.dispatch import receiver
from purchase.models import Invoice,InvoiceItem,Payment,PaymentLine
from product.models import Stree,Stock,StockTransaction
from django.contrib.contenttypes.models import ContentType

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

@receiver(signals.pre_delete,sender = InvoiceItem)
def remove_stock(sender,instance,*args,**kwargs):
    print('removing associated created stock')
    if instance.invoice.posted:
        instance.unpost()
#     if instance.is_return:
#         if 'Lot' in instance.product.name:
#             pass
#         else :
#             pass
#     else:
#         if 'Lot' in instance.product.name:
#             stock = Stock.objects.get(variant = instance.product)
#             stock.remove(
#             instance.weight,instance.quantity,
#             instance.weight,instance.quantity,
#             cto = instance.invoice,
#             at = 'PR'
#             )
#         else:
#             # Pass the instance we created in the snippet above
#             ct = ContentType.objects.get_for_model(instance.invoice)
#
#             # Get the list of likes
#             txns = StockTransaction.objects.filter(content_type=ct,
#                                                 object_id=instance.invoice.id,
#                                                 # activity_type=StockTransaction.PURCHASE,
#                                                 stock__weight = instance.weight,
#                                                 stock__quantity= instance.quantity,
#                                                 )
#
#             txns[0].stock.remove(
#             instance.weight,instance.quantity,
#             instance.weight,instance.quantity,
#             cto = instance.invoice,
#             at = 'PR'
#             )uncomment till here remove_Stock incase post unpost doesnt work as ex[ected]


    # # filter more accurately by stock_transaction_content_object =instance i.e invoice
    # node = Stock.objects.get(created__date = instance.invoice.created,
    #                             # stocktransaction__content_object  = instance,
    #                             variant = instance.product)
    #
    # if instance.is_return:
    #     # remove from is return
    #     if node.tracking_type =='Lot':
    #
    #         # add to stock
    #         node.weight +=instance.weight
    #         node.quantity +=instance.quantity
    #         node.Qih += instance.quantity
    #         node.Wih +=insance.weight
    #         node.save()
    #         node.update_status()
    #         stock_transaction = StockTransaction.objects.create(
    #                                     stock=stock,
    #                                     activity_type = 'PR',
    #                                     content_object = instance.invoice,
    #                                     type = 'IN',
    #                                     quantity = instance.quantity,
    #                                     weight = instance.weight)
    #         print('Removed lot from Return and added to Stock')
    #     else:
    #         print("You need to merge stock to lot and return via purchase return.")
    #
    # else:
    #     # remove from stock
    #     if node.tracking_type =='Lot':
    #
    #         node.weight -= instance.weight
    #         node.quantity -= instance.quantity
    #         node.Wih -= instance.weight
    #         node.Qih -= instance.quantity
    #
    #         node.save()
    #         node.update_status()
    #         stock_transaction = StockTransaction.objects.create(
    #                                     stock=node,
    #                                     activity_type = 'PR',
    #                                     content_object = instance.invoice,
    #                                     type = 'OUT',
    #                                     quantity = instance.quantity,
    #                                     weight = instance.weight)
    #         print('Removed from Stock lot')
    #     else:
    #         node.delete()
    #         print('Deleted from stock unique')
