from django.db import models
from django.contrib.postgres.fields import DateRangeField

# Create your models here.
class NoticeGroup(models.Model):
    name = models.CharField(max_length=30,unique =True)
    date_range = DateRangeField()
    

    class Meta:
        pass

    def __str__(self):
        return f"{self.id} {self.name}"
    
    def get_absolute_url(self):
        return reverse("notify_groupnotice_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("notify_groupnotice_update", args=(self.pk,))

    def items_count(self):
        return self.notice_items.count()

    def create_notice(self):
        pass
    def delete_all_notice(self):
        pass
    def delete_notice(self):
        pass
    def print_notice(self):
        pass

class Notification(models.Model):

    # relationships
    group = models.ForeignKey("notify.NoticeGroup",
                    null = True, blank = True,
                    on_delete = models.CASCADE,
                    related_name = "notice_items")
    loan = models.ForeignKey("girvi.Loan", 
                    on_delete=models.CASCADE,
                    related_name="notifications")

    # fields
    
    class MediumType(models.TextChoices):
        Post = "P", "Post"
        Whatsapp = "W", "Whatsapp"
        SMS = "S", "SMS"

    medium_type = models.CharField(
        max_length=1, choices=MediumType.choices, default=MediumType.Post
    )

    class NoticeType(models.TextChoices):
        First_Reminder = "FR","First Reminder"
        Second_Reminder = "SR","Second Reminder"
        Final_Notice = "FN","Final Notice"
        Loan_created = "LN","Loan Created"

    notice_type = models.CharField(
        max_length=2, choices=NoticeType.choices, default=NoticeType.First_Reminder
    )

    class StatusType(models.TextChoices):
        Draft = "D", "Draft"
        Sent = "S", "Sent"
        Delivered = "Z","Delivered"
        Acknowledged = "A", "Acknowledged"
        Responded = "R", "Responded"

    status = models.CharField(
        max_length=1, choices=StatusType.choices, default=StatusType.Draft
    )

    last_updated = models.DateTimeField(auto_now=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        unique_together = ('loan', 'notice_type',)

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        return reverse("notify_Notification_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("notify_Notification_update", args=(self.pk,))

    def create(self):
        pass
    def update_status(self):
        pass