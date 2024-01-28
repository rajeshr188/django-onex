from django.db.models import signals
from django.db.models.signals import post_save
from django.dispatch import receiver

from dea.models import JournalEntry
from sales.models import Invoice, InvoiceItem, Receipt, ReceiptAllocation

# @receiver(signals.post_delete, sender=ReceiptAllocation)
# def delete_status(sender, instance, *args, **kwargs):
#     print("deleting invoice status")
#     inv = instance.invoice
#     print(f"in bal :{inv.get_balance()}")
#     if inv.get_balance() == inv.balance:
#         inv.status = "Unpaid"
#     else:
#         inv.status = "PartialPaid"
#     inv.save()


# @receiver(post_save, sender=Invoice)
@receiver(post_save, sender=Receipt)
def create_sales_journal(sender, instance, created, **kwargs):
    # lt, at = instance.get_transactions()
    if created:
        print("newly created journal")
        # lj, aj = instance.create_journals()
        # lj.transact(lt)
        # aj.transact(at)
        instance.create_transactions()

    else:
        print("existing journal:appending txns")
        # lj, aj = instance.get_journals()
        # lj.untransact(lt)
        # aj.untransact(at)
        # lj.transact(lt)
        # aj.transact(at)
        instance.reverse_transactions()
        instance.create_transactions()
    return instance


@receiver(post_save, sender=InvoiceItem)
# @receiver(post_save, sender=PaymentAllocation)
def create_stock_journal(sender, instance, created, **kwargs):
    if created:
        print("newly created stock journal")
        sj = instance.create_journal()
        instance.post(sj)
        instance.invoice.create_transactions()

    else:
        print("existing stock journal:appending txns")
        sj = instance.get_journal()
        instance.unpost(sj)
        instance.post(sj)
        instance.invoice.reverse_transactions()
        instance.invoice.create_transactions()
    return instance
