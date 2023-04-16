from django.db.models.signals import post_save
from django.dispatch import receiver
from product.models import StockLot

@receiver(post_save, sender=StockLot)
def generate_barcode(sender, instance, created, **kwargs):
    if created:
        instance.generate_barcode()