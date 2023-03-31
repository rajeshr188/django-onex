from django.db import models
class PricingTier(models.Model):
    """
    base-tier will have basic purchase and selling price for the product-variants,
    consequent tiers can derive from base-tier and modify a set of price for the set of products
    """

    name = models.CharField(max_length=255)
    contact = models.ForeignKey("contact.Customer", on_delete=models.CASCADE)
    minimum_quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name}"


class Price(models.Model):
    """
    price for each product variant that will be used by stock in determining selling/purchasing
    price based on the tier the customer belongs to
    """

    product = models.ForeignKey('ProductVariant', on_delete=models.CASCADE)
    contact = models.ForeignKey("contact.Customer", on_delete=models.CASCADE)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_tier = models.ForeignKey(PricingTier, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product} : {self.selling_price} {self.purchase_price}"
