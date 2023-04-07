# Generated by Django 4.2rc1 on 2023-04-06 17:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0012_alter_pricingtierproductprice_pricing_tier"),
        ("approval", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="approval",
            name="status",
            field=models.CharField(
                choices=[
                    ("Pending", "Pending"),
                    ("Complete", "Complete"),
                    ("Billed", "Billed"),
                ],
                default="Pending",
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="approvalline",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="approval_lineitems",
                to="product.stocklot",
            ),
        ),
    ]