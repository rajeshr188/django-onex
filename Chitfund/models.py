from django.urls import reverse
from django_extensions.db.fields import AutoSlugField
from django.db.models import CharField
from django.db.models import DateField
from django.db.models import DateTimeField
from django.db.models import PositiveIntegerField
from django.db.models import PositiveSmallIntegerField
from django_extensions.db.fields import AutoSlugField
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth import models as auth_models
from django.db import models as models
from django_extensions.db import fields as extension_fields
from datetime import datetime
from django.utils import timezone
class Contact(models.Model):

    # Fields
    name = models.CharField(max_length=255,unique=True)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    phoneno = models.CharField(max_length=10)


    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('contact_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('contact_update', args=(self.slug,))

    def get_noofchits(self):
        return Chit.objects.filter(members=self).count()

class Chit(models.Model):

    # Fields
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    type = models.CharField(max_length=30)
    amount = models.PositiveIntegerField()
    commission = models.PositiveIntegerField()
    member_limit = models.PositiveSmallIntegerField()
    date_to_allot = models.DateField()

    # Relationship Fields
    owner = models.OneToOneField(
        'Contact',
        on_delete=models.CASCADE,related_name='owner'
    )
    members = models.ManyToManyField(
        'Contact',related_name='members'
    )

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('chit_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('chit_update', args=(self.slug,))

    def get_noofallotments(self):
        return self.allotment_set.count()

    def get_noofallotments_rem(self):
        return self.get_noofmembers()-self.get_noofallotments()

    def get_noofmembers(self):
        return self.members.count()

    def get_commission_amount(self):
        return (self.amount*self.commission)/100

class Collection(models.Model):

    # Fields
    slug = extension_fields.AutoSlugField(populate_from='member', blank=True)
    date_collected = models.DateTimeField(default=timezone.now)
    amount = models.PositiveIntegerField()

    # Relationship Fields
    allotment = models.ForeignKey(
        'Allotment',
        on_delete=models.CASCADE
    )
    member = models.ForeignKey(
        'Contact',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ('-pk',)

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('collection_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('collection_update', args=(self.slug,))


class Allotment(models.Model):

    # Fields
    name=models.CharField(max_length=100)
    amount = models.PositiveIntegerField()
    installment=models.PositiveIntegerField()
    slug = extension_fields.AutoSlugField(populate_from='to_member', blank=True)
    created = models.DateTimeField(default=timezone.now)

    # Relationship Fields
    chit = models.ForeignKey(
        'Chit',
        on_delete=models.CASCADE
    )
    to_member = models.ForeignKey(
        'Contact',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('allotment_detail', args=(self.slug,))

    def get_update_url(self):
        return reverse('allotment_update', args=(self.slug,))
