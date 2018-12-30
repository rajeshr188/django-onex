from django.db.models import signals
from django.dispatch import receiver
from sales.models import Invoice,Receipt,ReceiptLine

@receiver(signals.pre_delete,sender=ReceiptLine)
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
