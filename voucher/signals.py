
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from myapp.models import Transaction, Voucher


@receiver(pre_save, sender=Voucher)
def voucher_pre_save(sender, instance, **kwargs):
    if instance.pk:
        # instance is being updated, save the old balance
        instance._old_balance = Voucher.objects.get(pk=instance.pk).balance


@receiver(post_save, sender=Voucher)
def voucher_post_save(sender, instance, created, **kwargs):
    if not created:
        # instance is being updated, unpost and post transactions using old and new balances
        old_balance = getattr(instance, "_old_balance", None)
        if old_balance is not None and old_balance != instance.balance:
            # balance has changed, unpost and post transactions
            Transaction.objects.filter(voucher=instance).unpost()
            transaction = Transaction(voucher=instance, amount=instance.balance)
            transaction.post()
            instance._old_balance = instance.balance
        else:
            # balance has not changed, do nothing
            pass
    else:
        # instance is being created, post the transaction
        transaction = Transaction(voucher=instance, amount=instance.balance)
        transaction.post()
