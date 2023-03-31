# Generated by Django 4.2rc1 on 2023-03-31 08:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("girvi", "0001_initial"),
        ("contact", "0001_initial"),
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
                ("description", models.TextField(blank=True, null=True)),
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
                        choices=[
                            ("P", "Post"),
                            ("W", "Whatsapp"),
                            ("S", "SMS"),
                            ("L", "Letter"),
                        ],
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
                ("message", models.TextField()),
                ("is_printed", models.BooleanField(default=False)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contact.customer",
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="notify.noticegroup",
                    ),
                ),
                ("loans", models.ManyToManyField(to="girvi.loan")),
            ],
        ),
    ]
