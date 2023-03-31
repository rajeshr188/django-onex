# Generated by Django 4.2rc1 on 2023-03-31 08:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Approval",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "total_wt",
                    models.DecimalField(decimal_places=3, default=0, max_digits=10),
                ),
                ("total_qty", models.IntegerField(default=0)),
                ("posted", models.BooleanField(default=False)),
                ("is_billed", models.BooleanField(default=False)),
                (
                    "status",
                    models.CharField(
                        choices=[("Pending", "Pending"), ("Complete", "Complete")],
                        default="Pending",
                        max_length=10,
                    ),
                ),
            ],
            options={
                "ordering": ("created_at",),
            },
        ),
        migrations.CreateModel(
            name="ApprovalLine",
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
                ("quantity", models.IntegerField(default=0)),
                (
                    "weight",
                    models.DecimalField(decimal_places=3, default=0.0, max_digits=10),
                ),
                (
                    "touch",
                    models.DecimalField(decimal_places=3, default=0.0, max_digits=10),
                ),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Pending", "Pending"),
                            ("Returned", "Returned"),
                            ("Billed", "Billed"),
                        ],
                        default="Pending",
                        max_length=30,
                    ),
                ),
                (
                    "approval",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="approval.approval",
                    ),
                ),
            ],
            options={
                "ordering": ("approval",),
            },
        ),
        migrations.CreateModel(
            name="ApprovalLineReturn",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("quantity", models.IntegerField(default=0)),
                (
                    "weight",
                    models.DecimalField(decimal_places=3, default=0.0, max_digits=10),
                ),
                ("posted", models.BooleanField(default=False)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "line",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="approval.approvalline",
                    ),
                ),
            ],
            options={
                "ordering": ("id",),
            },
        ),
    ]
