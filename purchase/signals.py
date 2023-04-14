from django.db.models import signals
from django.db.models.signals import post_save
from django.dispatch import receiver

from dea.models import Journal
from purchase.models import Invoice, InvoiceItem, Payment, PaymentAllocation


@receiver(signals.pre_delete, sender=PaymentAllocation)
def delete_status(sender, instance, *args, **kwargs):
    print("deleting invoice status")
    inv = instance.invoice
    if inv.balance - instance.allocated_amount == 0:
        inv.status = "Unpaid"
    elif inv.balance - instance.allocated_amount > 0:
        inv.status = "PartiallyPaid"
    else:
        inv.status = "Error"
    inv.save()


@receiver(post_save, sender=Invoice)
@receiver(post_save, sender=Payment)
def create_journal(sender, instance, created, **kwargs):
    lt, at = instance.get_transactions()
    if created:
        lj, aj = instance.create_journals()
        lj.transact(lt)
        aj.transact(at)
    else:
        lj, aj = instance.get_journals()
        lj.untransact(lt)
        aj.untransact(at)
        lj.transact(lt)
        aj.transact(at)
    return instance


@receiver(post_save, sender=InvoiceItem)
# @receiver(post_save, sender=PaymentAllocation)
def create_stock_journal(sender, instance, created, **kwargs):
    if created:
        print("newly created stock journal")
        sj = instance.create_journal()
        instance.post(sj)
    else:
        print("existing stock journal:appending txns")
        sj = instance.get_journal()
        instance.unpost(sj)
        instance.post(sj)
    return instance
