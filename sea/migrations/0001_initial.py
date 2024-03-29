# Generated by Django 4.2.3 on 2024-02-15 10:37

import django.contrib.postgres.fields.ranges
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Account",
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
                ("name", models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="Book",
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
                ("name", models.CharField(max_length=20)),
                ("daterange", django.contrib.postgres.fields.ranges.DateRangeField()),
                (
                    "book_type",
                    models.CharField(
                        choices=[
                            ("Daily", "Daily"),
                            ("Monthly", "Monthly"),
                            ("Yearly", "Yearly"),
                        ],
                        max_length=10,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Transaction",
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
                ("date", models.DateField(db_index=True)),
                (
                    "txn_type",
                    models.CharField(
                        choices=[("Cr", "Credit"), ("Dr", "Debit")], max_length=2
                    ),
                ),
                ("amount", models.DecimalField(decimal_places=3, max_digits=14)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="sea.account"
                    ),
                ),
            ],
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
                ("created", models.DateField()),
                (
                    "closing_balance",
                    models.DecimalField(decimal_places=3, max_digits=14),
                ),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="sea.account"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="drs",
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
                ("period", django.contrib.postgres.fields.ranges.DateTimeRangeField()),
                ("cb", models.DecimalField(decimal_places=3, max_digits=14)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="sea.account"
                    ),
                ),
            ],
        ),
    ]
