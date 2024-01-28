from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from approval.models import ApprovalLine, ReturnItem
from dea.models import JournalEntry


@receiver(post_save, sender=ApprovalLine)
@receiver(post_save, sender=ReturnItem)
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

    # instance.update_status()
    return instance


@receiver(pre_save, sender=ApprovalLine)
def update_approvalline_status(sender, instance, **kwargs):
    instance.status = instance.update_status()
    instance.approval.update_status()


# receiver for predelete to run instance.line_item.unpost()
@receiver(post_delete, sender=ReturnItem)
def update_returnitem_status(sender, instance, **kwargs):
    instance.line_item.update_status()
