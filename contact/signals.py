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
    if created:
        acct_c = AccountType_Ext.objects.get(description = 'Creditor')
        acct_d = AccountType_Ext.objects.get(description = 'Debtor')
        entity_t = EntityType.objects.get(name="Person")
        if instance.type == "Wh" or instance.type =="Re":
            Account.objects.create(contact = instance,
                entity = entity_t,
                AccountType_Ext = acct_d)
        else:
             Account.objects.create(contact = instance,
                entity = entity_t,
                AccountType_Ext = acct_c)
