# Generated by Django 4.0.2 on 2022-02-15 04:38

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PaymentTerm",
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
                ("name", models.CharField(max_length=30)),
                ("description", models.TextField()),
                ("due_days", models.PositiveSmallIntegerField()),
                ("discount_days", models.PositiveSmallIntegerField()),
                ("discount", models.DecimalField(decimal_places=2, max_digits=10)),
            ],
            options={
                "ordering": ("due_days",),
            },
        ),
        migrations.CreateModel(
            name="voucher",
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
            ],
        ),
    ]