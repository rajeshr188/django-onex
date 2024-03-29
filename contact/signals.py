from django.db.models.signals import post_save
from django.dispatch import receiver

from dea.models import Account, AccountType_Ext, EntityType

from .models import Customer


@receiver(post_save, sender=Customer)
def add_account(sender, instance, created, **kwargs):
    acct_c = AccountType_Ext.objects.get(description="Creditor")
    acct_d = AccountType_Ext.objects.get(description="Debtor")
    try:
        acc = instance.account
    except Account.DoesNotExist:
        acc = None
    if created or acc is None:
        entity_t = EntityType.objects.get(name="Person")
        if instance.customer_type == "Wh" or instance.customer_type == "Re":
            Account.objects.create(
                contact=instance, entity=entity_t, AccountType_Ext=acct_d
            )
        else:
            Account.objects.create(
                contact=instance, entity=entity_t, AccountType_Ext=acct_c
            )
    else:
        if instance.customer_type == "Wh" or instance.customer_type == "Re":
            instance.account.AccountType_Ext = acct_d
        else:
            instance.account.AccountType_Ext = acct_c
        instance.account.save(update_fields=["AccountType_Ext"])
