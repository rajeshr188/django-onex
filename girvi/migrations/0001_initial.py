# Generated by Django 4.2.3 on 2024-02-15 10:37

import datetime
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="License",
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
                ("name", models.CharField(max_length=255)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("PBL", "Pawn Brokers License"),
                            ("GST", "Goods & Service Tax"),
                        ],
                        default="PBL",
                        max_length=30,
                    ),
                ),
                ("shopname", models.CharField(max_length=30)),
                ("address", models.TextField(max_length=100)),
                ("phonenumber", models.CharField(max_length=30)),
                ("propreitor", models.CharField(max_length=30)),
                ("renewal_date", models.DateField()),
            ],
            options={
                "ordering": ("-created",),
            },
        ),
        migrations.CreateModel(
            name="Loan",
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
                ("desc", models.TextField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("loan_date", models.DateTimeField(default=datetime.datetime.now)),
                ("lid", models.IntegerField(blank=True, null=True)),
                (
                    "loan_id",
                    models.CharField(db_index=True, max_length=255, unique=True),
                ),
                ("has_collateral", models.BooleanField(default=False)),
                (
                    "pic",
                    models.ImageField(blank=True, null=True, upload_to="loan_pics/"),
                ),
                (
                    "loan_type",
                    models.CharField(
                        blank=True,
                        choices=[("Taken", "Taken"), ("Given", "Given")],
                        default="Given",
                        max_length=10,
                        null=True,
                    ),
                ),
                (
                    "item_desc",
                    models.TextField(
                        blank=True, max_length=100, null=True, verbose_name="Item"
                    ),
                ),
                (
                    "loan_amount",
                    models.PositiveIntegerField(
                        blank=True, default=0, null=True, verbose_name="Amount"
                    ),
                ),
                (
                    "interest",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0,
                        max_digits=10,
                        null=True,
                    ),
                ),
            ],
            options={
                "ordering": ("series", "lid"),
                "get_latest_by": "id",
            },
        ),
        migrations.CreateModel(
            name="LoanItem",
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
                    "pic",
                    models.ImageField(blank=True, null=True, upload_to="loan_pics/"),
                ),
                (
                    "itemtype",
                    models.CharField(
                        choices=[
                            ("Gold", "Gold"),
                            ("Silver", "Silver"),
                            ("Bronze", "Bronze"),
                        ],
                        default="Gold",
                        max_length=30,
                    ),
                ),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("weight", models.DecimalField(decimal_places=3, max_digits=10)),
                (
                    "purity",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=75,
                        max_digits=10,
                        null=True,
                    ),
                ),
                ("loanamount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("interestrate", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "interest",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0,
                        max_digits=10,
                        null=True,
                    ),
                ),
                (
                    "itemdesc",
                    models.TextField(
                        blank=True, max_length=100, null=True, verbose_name="Item"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="LoanPayment",
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
                ("desc", models.TextField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("payment_date", models.DateTimeField()),
                (
                    "payment_amount",
                    models.DecimalField(
                        decimal_places=2, max_digits=10, verbose_name="Payment"
                    ),
                ),
                (
                    "principal_payment",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "interest_payment",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                ("with_release", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ("-id",),
            },
        ),
        migrations.CreateModel(
            name="Release",
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
                    "release_date",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "release_id",
                    models.CharField(
                        blank=True, max_length=255, null=True, unique=True
                    ),
                ),
            ],
            options={
                "ordering": ("-id",),
            },
        ),
        migrations.CreateModel(
            name="Series",
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
                    "name",
                    models.CharField(
                        blank=True, default="", max_length=30, unique=True
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ("created",),
            },
        ),
        migrations.CreateModel(
            name="Statement",
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
                ("created", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="StatementItem",
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
                    "loan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="girvi.loan"
                    ),
                ),
                (
                    "statement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="girvi.statement",
                    ),
                ),
            ],
        ),
    ]
