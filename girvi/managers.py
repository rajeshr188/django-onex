from django.db import models

class LoanManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('series','release','customer')

class ReleasedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(release__isnull = False)

class UnReleasedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(release__isnull = True)

class ReleaseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('loan')
