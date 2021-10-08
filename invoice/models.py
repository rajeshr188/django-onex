from django.db import models

# Create your models here.
class PaymentTerm(models.Model):
    name = models.CharField(max_length=30)
    description = models.TextField()
    due_days = models.PositiveSmallIntegerField()
    discount_days = models.PositiveSmallIntegerField()
    discount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ('due_days',)

    def __str__(self):
        return f"{self.name} ({self.due_days})"
