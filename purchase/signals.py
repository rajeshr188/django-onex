from django.db.models import signals
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from dea.models import JournalEntry
from purchase.models import Invoice, InvoiceItem, Payment, PaymentAllocation

# @receiver(signals.pre_delete, sender=PaymentAllocation)
# def delete_status(sender, instance, *args, **kwargs):
#     print("updating purchase status")
#     inv = instance.invoice
#     inv.update_status()


@receiver(post_save, sender=Invoice)
@receiver(post_save, sender=Payment)
def create_purchase_journal(sender, instance, created, **kwargs):
    if created:
        instance.create_transactions()
    else:
        instance.reverse_transactions()
        instance.create_transactions()
    return instance


@receiver(pre_save, sender=InvoiceItem)
def pre_save_voucher(sender, instance, **kwargs):
    print(f"Balance before update: {instance.cash_balance}")
    print(f"Balance before update: {instance.metal_balance}")


@receiver(post_save, sender=InvoiceItem)
# @receiver(post_save, sender=Payment)
def create_stock_journal(sender, instance, created, **kwargs):
    print(f"Balance after update: {instance.cash_balance}")
    print(f"Balance after update: {instance.metal_balance}")
    if created:
        print("newly created stock journal")
        
        instance.post()
        instance.invoice.create_transactions()
    else:
        print("existing stock journal:appending txns")
        
        instance.unpost()
        instance.post()
        # instance.invoice.update_balance()
        instance.invoice.reverse_transactions()
        instance.invoice.create_transactions()

    return instance
