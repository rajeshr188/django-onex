from django.db import models
from djmoney.models.fields import MoneyField

# balance = MoneyField(max_digits=14, decimal_places=2, default_currency='USD')


class RateSource(models.Model):
    name = models.CharField(max_length=30)
    location = models.CharField(max_length=30)
    tax_included = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Rate(models.Model):
    class Metal(models.TextChoices):
        GOLD = "Gold", "Gold"
        SILVER = "Silver", "Silver"

    class Currency(models.TextChoices):
        INR = "INR", "INR"
        USD = "USD", "USD"

    class Purity(models.TextChoices):
        K24 = "24k", "24K"
        K22 = "22k", "22K"
        K18 = "18k", "18K"
        K14 = "14k", "14K"
        K10 = "10k", "10K"

    metal = models.CharField(max_length=6, choices=Metal.choices, default=Metal.GOLD)
    currency = models.CharField(
        max_length=3, choices=Currency.choices, default=Currency.INR
    )
    purity = models.CharField(max_length=3, choices=Purity.choices, default=Purity.K24)
    buying_rate = models.DecimalField(max_digits=10, decimal_places=2)
    selling_rate = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    # related Fields
    rate_source = models.ForeignKey("RateSource", on_delete=models.CASCADE)

    class Meta:
        unique_together = ["metal", "currency", "timestamp", "purity"]

    def __str__(self):
        return f" {self.timestamp.date()} {self.metal} {self.purity} {self.buying_rate} {self.selling_rate}"

    def get_absolute_url(self):
        return reverse("rate_detail", kwargs={"pk": self.pk})
