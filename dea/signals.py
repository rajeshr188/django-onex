from django.db.models.signals import (post_delete, post_save, pre_delete,
                                      pre_save)
from django.dispatch import receiver

from dea.models import Journal, JournalEntry

# @receiver(pre_save, sender=Journal)
# def reverse_journal_entry(sender, instance, **kwargs):
#     # Access model and subclass:
#     model_name = instance._meta.model_name
#     subclass_name = instance.polymorphic_ctype.name
#     # Perform reversal logic based on model and subclass as needed
#     print(f"Reversing journal entry for {model_name} subclass {subclass_name}: {instance}")
#     if instance.pk:  # If journal is being updated
#         # Retrieve the old data from the database
#         old_instance = sender.objects.get(pk=instance.pk)

#         if old_instance.is_changed(instance):
#             old_instance.reverse_transactions()
#             print("Journal reversed")
#         else:
#             print("No change in Journal")

# @receiver(post_save, sender=Journal)
# def create_journal_entry(sender, instance, **kwargs):
#     print("create_journal_entry Post_save signal")
#     instance.create_transactions()
