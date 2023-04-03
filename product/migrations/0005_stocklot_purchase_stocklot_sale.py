# Generated by Django 4.2rc1 on 2023-04-01 17:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0001_initial"),
        ("sales", "0001_initial"),
        ("product", "0004_alter_stocklot_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="stocklot",
            name="purchase",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="purchase.invoice",
            ),
        ),
        migrations.AddField(
            model_name="stocklot",
            name="sale",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="sales.invoice",
            ),
        ),
    ]