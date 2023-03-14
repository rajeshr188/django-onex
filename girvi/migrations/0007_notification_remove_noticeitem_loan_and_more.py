# Generated by Django 4.1.5 on 2023-03-02 13:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("girvi", "0006_remove_loanitem_rate_remove_notice_customer_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "medium_type",
                    models.CharField(
                        choices=[("P", "Post"), ("W", "Whatsapp")],
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
                    "loan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="girvi.loan"
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="noticeitem",
            name="loan",
        ),
        migrations.RemoveField(
            model_name="noticeitem",
            name="notice",
        ),
        migrations.DeleteModel(
            name="Notice",
        ),
        migrations.DeleteModel(
            name="NoticeItem",
        ),
    ]