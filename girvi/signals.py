from django.db.models.signals import post_save
from actstream import action
from .models import Loan

# MyModel has been registered with actstream.registry.register

def my_handler(sender, instance, created, **kwargs):
    action.send(instance, verb='was saved')

post_save.connect(my_handler, sender=Loan)
