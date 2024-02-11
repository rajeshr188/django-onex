from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.shortcuts import reverse
from django.utils import timezone
from moneyed import Money

from contact.models import Customer

from ..models import LoanPayment


class ReleaseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("loan")


class Release(models.Model):
    # Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    release_date = models.DateTimeField(default=timezone.now)
    release_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    released_by = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        related_name="released_by",
        null=True,
        blank=True,
    )
    # Relationship Fields
    loan = models.OneToOneField(
        "girvi.Loan", on_delete=models.CASCADE, related_name="release"
    )
    objects = ReleaseManager()

    class Meta:
        ordering = ("-id",)

    def __str__(self):
        return f"{self.release_id}"

    def get_absolute_url(self):
        return reverse("girvi:girvi_release_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("girvi:girvi_release_update", args=(self.pk,))

    def generate_release_id(self):
        last_release = Release.objects.all().order_by("id").last()
        if not last_release:
            return "R0001"
        release_id = last_release.release_id
        release_int = int(release_id.split("R")[-1])
        new_release_int = release_int + 1
        new_release_id = "R" + str(new_release_int).zfill(4)
        return new_release_id

    def save(self, *args, **kwargs):
        if not self.release_id:
            self.release_id = self.generate_release_id()
        super().save(*args, **kwargs)
