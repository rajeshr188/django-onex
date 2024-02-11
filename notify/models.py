from django.contrib.postgres.fields import DateRangeField
from django.db import models
from django.shortcuts import reverse

from girvi.models import Loan


# Create your models here.
class NoticeGroup(models.Model):
    name = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        pass

    def __str__(self):
        return f"{self.id} {self.name}"

    def get_absolute_url(self):
        return reverse("notify_noticegroup_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("notify_noticegroup_update", args=(self.pk,))

    def items_count(self):
        return self.notice_items.count()

    def print_notice(self):
        pass


class Notification(models.Model):
    # relationships
    group = models.ForeignKey(
        "notify.NoticeGroup",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    customer = models.ForeignKey("contact.Customer", on_delete=models.CASCADE)
    loans = models.ManyToManyField(Loan, related_name="notifications")

    # fields

    class MediumType(models.TextChoices):
        Post = "P", "Post"
        Whatsapp = "W", "Whatsapp"
        SMS = "S", "SMS"
        Letter = "L", "Letter"

    medium_type = models.CharField(
        max_length=1, choices=MediumType.choices, default=MediumType.Post
    )

    class NoticeType(models.TextChoices):
        First_Reminder = "FR", "First Reminder"
        Second_Reminder = "SR", "Second Reminder"
        Final_Notice = "FN", "Final Notice"
        Loan_created = "LN", "Loan Created"

    notice_type = models.CharField(
        max_length=2, choices=NoticeType.choices, default=NoticeType.First_Reminder
    )

    class StatusType(models.TextChoices):
        Draft = "D", "Draft"
        Sent = "S", "Sent"
        Delivered = "Z", "Delivered"
        Acknowledged = "A", "Acknowledged"
        Responded = "R", "Responded"

    status = models.CharField(
        max_length=1, choices=StatusType.choices, default=StatusType.Draft
    )
    message = models.TextField()
    is_printed = models.BooleanField(default=False)

    last_updated = models.DateTimeField(auto_now=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        # unique_together = ('loan', 'notice_type',)
        pass

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        return reverse("notify_notification_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("notify_Notification_update", args=(self.pk,))

    def update_status(self):
        pass

    def print_letter(self):
        pass

    def send_sms(self):
        # implementation for sending an SMS
        pass

    def send_notification(self):
        if self.notification_type == "Letter":
            self.print_letter()
        elif self.notification_type == "SMS":
            self.send_sms()
        elif self.notification_type == "WhatsApp":
            # implementation for sending a WhatsApp message
            pass
