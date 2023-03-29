# Generated by Django 4.2rc1 on 2023-03-29 01:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        (
            "product",
            "0002_stockbalance_movement_stocklot_remove_stock_barcode_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="stockstatement",
            name="lot",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="product.stocklot",
            ),
        ),
    ]