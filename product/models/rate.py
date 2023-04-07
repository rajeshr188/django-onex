from django.db import models


class RateSource(models.Model):
    name = models.CharField(max_length=30)
    location = models.CharField(max_length=30)
    tax_included = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Rate(models.Model):
    GOLD = "gold"
    SILVER = "silver"
    METAL_CHOICES = [
        (GOLD, "Gold"),
        (SILVER, "Silver"),
    ]
    INR = "INR"
    USD = "USD"
    CURRENCY_CHOICES = [
        (INR, "INR"),
        (USD, "USD"),
    ]
    PURITY_CHOICES = [
        ("24k", "24K"),
        ("22k", "22K"),
        ("18k", "18K"),
        ("14k", "14K"),
        ("10k", "10K"),
    ]
    metal = models.CharField(max_length=6, choices=METAL_CHOICES)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    purity = models.CharField(max_length=3, choices=PURITY_CHOICES)
    buying_rate = models.DecimalField(max_digits=10, decimal_places=2)
    selling_rate = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    # related Fields
    rate_source = models.ForeignKey("RateSource", on_delete=models.CASCADE)

    class Meta:
        unique_together = ["metal", "currency", "timestamp", "purity"]

    def __str__(self):
        return f" {self.timestamp} {self.metal} {self.purity} {self.rate}"

    # def get_absolute_url(self):
    #     return reverse("rate_detail", kwargs={"pk": self.pk})
    

