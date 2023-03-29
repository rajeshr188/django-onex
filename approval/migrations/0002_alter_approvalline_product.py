# Generated by Django 4.2rc1 on 2023-03-29 01:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        (
            "product",
            "0002_stockbalance_movement_stocklot_remove_stock_barcode_and_more",
        ),
        ("approval", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="approvalline",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="product",
                to="product.stocklot",
            ),
        ),
    ]
