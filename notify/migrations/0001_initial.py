# Generated by Django 4.1.5 on 2023-03-05 19:05

import django.contrib.postgres.fields.ranges
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("girvi", "0009_alter_notification_unique_together_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="NoticeGroup",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=30, unique=True)),
                ("date_range", django.contrib.postgres.fields.ranges.DateRangeField()),
            ],
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "medium_type",
                    models.CharField(
                        choices=[("P", "Post"), ("W", "Whatsapp"), ("S", "SMS")],
                        default="P",
                        max_length=1,
                    ),
                ),
                (
                    "notice_type",
                    models.CharField(
                        choices=[
                            ("FR", "First Reminder"),
                            ("SR", "Second Reminder"),
                            ("FN", "Final Notice"),
                            ("LN", "Loan Created"),
                        ],
                        default="FR",
                        max_length=2,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("D", "Draft"),
                            ("S", "Sent"),
                            ("Z", "Delivered"),
                            ("A", "Acknowledged"),
                            ("R", "Responded"),
                        ],
                        default="D",
                        max_length=1,
                    ),
                ),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "group",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notice_items",
                        to="notify.noticegroup",
                    ),
                ),
                (
                    "loan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to="girvi.loan",
                    ),
                ),
            ],
            options={
                "unique_together": {("loan", "notice_type")},
            },
        ),
    ]