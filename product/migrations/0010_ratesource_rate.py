# Generated by Django 4.2rc1 on 2023-04-02 08:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0009_rename_pricint_tier_pricingtierproductprice_pricing_tier"),
    ]

    operations = [
        migrations.CreateModel(
            name="RateSource",
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
                ("location", models.CharField(max_length=30)),
                ("tax_included", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="Rate",
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
                    "metal",
                    models.CharField(
                        choices=[("gold", "Gold"), ("silver", "Silver")], max_length=6
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        choices=[("INR", "INR"), ("USD", "USD")], max_length=3
                    ),
                ),
                (
                    "purity",
                    models.CharField(
                        choices=[
                            ("24k", "24K"),
                            ("22k", "22K"),
                            ("18k", "18K"),
                            ("14k", "14K"),
                            ("10k", "10K"),
                        ],
                        max_length=3,
                    ),
                ),
                ("rate", models.DecimalField(decimal_places=2, max_digits=10)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "rate_source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="product.ratesource",
                    ),
                ),
            ],
            options={
                "unique_together": {("metal", "currency", "timestamp", "purity")},
            },
        ),
    ]
