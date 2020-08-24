from django.db import models
from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from actstream.managers import ActionManager, stream

class MyActionManager(ActionManager):
    @stream
    def mystream(self, obj, verb='posted', time=None):
        if time is None:
            time = datetime.now()
        return obj.actor_actions.filter(verb = verb, timestamp__lte = time)

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
