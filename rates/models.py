from django.db import models

# Create your models here.
class Rate(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    on = models.DateTimeField()
    source = models.URLField()
    source_name = models.CharField(max_length=60)
    metal = models.CharField(max_length=20)
    price = models.DecimalField(decimal_places=4,max_digits=10)

    class Meta:
        get_latest_by = 'on'
        ordering = ['-on','metal']

    def __str__(self):
        return f"{self.on}-{self.metal}:{self.price}"