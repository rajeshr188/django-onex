from django.dispatch import receiver
from django.db.models.signals import post_save
from approval.models import ApprovalLine,ReturnItem
from dea.models import Journal

@receiver(post_save, sender=ApprovalLine)
@receiver(post_save, sender=ReturnItem)
def create_stock_journal(sender, instance, created, **kwargs):

    if created:
        print("newly created stock journal")
        sj = instance.create_journals()
        instance.post(sj)
    else:
        print("existing stock journal:appending txns")
        sj = instance.get_journals()
        instance.unpost(sj)
        instance.post(sj)
    return instance