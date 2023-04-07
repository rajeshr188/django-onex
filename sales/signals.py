from django.db.models import signals
from django.dispatch import receiver

from sales.models import ReceiptAllocation


@receiver(signals.post_delete, sender=ReceiptAllocation)
def delete_status(sender, instance, *args, **kwargs):
    print("deleting invoice status")
    inv = instance.invoice
    print(f"in bal :{inv.get_balance()}")
    if inv.get_balance() == inv.balance:
        inv.status = "Unpaid"
    else:
        inv.status = "PartialPaid"
    inv.save()
