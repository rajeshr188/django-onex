from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=StockLot)
def generate_barcode(sender, instance, created, **kwargs):
    instance.generate_barcode()