from django.db.models.signals import post_save,post_delete
from django.dispatch import receiver

from approval.models import ApprovalLine, ReturnItem
from dea.models import Journal


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


# receiver for predelete to run instance.line_item.unpost()
@receiver(post_delete, sender=ReturnItem)
def update_approvalline_status(sender, instance, **kwargs):
    print("delete stock journal")
    instance.line_item.update_status()
