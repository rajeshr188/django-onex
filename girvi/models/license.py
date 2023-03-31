from django.db import models

class License(models.Model):
    # Fields
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    lt = (("PBL", "Pawn Brokers License"), ("GST", "Goods & Service Tax"))
    type = models.CharField(max_length=30, choices=lt, default="PBL")
    shopname = models.CharField(max_length=30)
    address = models.TextField(max_length=100)
    phonenumber = models.CharField(max_length=30)
    propreitor = models.CharField(max_length=30)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return "%s" % self.name

    def get_absolute_url(self):
        return reverse("girvi_license_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("girvi_license_update", args=(self.pk,))

    def get_series_count(self):
        return self.series_set.count()


class Series(models.Model):
    name = models.CharField(max_length=30, default="", blank=True, unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True)
    license = models.ForeignKey(License, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("created",)
        unique_together = ["license", "name"]

    def __str__(self):
        return f"Series {self.name}"

    def get_absolute_url(self):
        return reverse("girvi_license_series_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("girvi_license_series_update", args=(self.pk,))

    def activate(self):
        self.is_active = not self.is_active
        self.save(update_fields=["is_active"])

    def loan_count(self):
        return self.loan_set.filter(release__isnull=True).count()

    def total_loan_amount(self):
        return self.loan_set.filter(release__isnull=True).aggregate(t=Sum("loanamount"))

    def total_gold_loan(self):
        return self.loan_set.filter(release__isnull=True, itemtype="Gold").aggregate(
            t=Sum("loanamount")
        )

    def total_silver_loan(self):
        return self.loan_set.filter(release__isnull=True, itemtype="Silver").aggregate(
            t=Sum("loanamount")
        )

    def total_gold_weight(self):
        return self.loan_set.filter(release__isnull=True, itemtype="Gold").aggregate(
            t=Sum("itemweight")
        )

    def total_silver_weight(self):
        return self.loan_set.filter(release__isnull=True, itemtype="Silver").aggregate(
            t=Sum("itemweight")
        )

