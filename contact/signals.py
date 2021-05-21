from django.db.models.signals import post_save
from actstream import action
from .models import Customer
from django.dispatch import receiver
from dea.models import Account, AccountType_Ext, EntityType
# MyModel has been registered with actstream.registry.register

def my_handler(sender, instance, created, **kwargs):
    action.send(instance, verb='was saved')

post_save.connect(my_handler, sender=Customer)


@receiver(post_save, sender=Customer)
def add_account(sender, instance, created,**kwargs):
    acct_c = AccountType_Ext.objects.get(description = 'Creditor')
    acct_d = AccountType_Ext.objects.get(description = 'Debtor')
    try:
        acc = instance.account
    except Account.DoesNotExist:
        acc = None
    if created or acc is None: 
        entity_t = EntityType.objects.get(name="Person")
        if instance.type == "Wh" or instance.type =="Re":
            Account.objects.create(contact = instance,
                entity = entity_t,
                AccountType_Ext = acct_d)
        else:
             Account.objects.create(contact = instance,
                entity = entity_t,
                AccountType_Ext = acct_c)
    else:
        if instance.type == "Wh" or instance.type =="Re":
            instance.account.AccountType_Ext = acct_d
        else:
            instance.account.AccountType_Ext = acct_c
        instance.account.save(update_fields=['AccountType_Ext'])

