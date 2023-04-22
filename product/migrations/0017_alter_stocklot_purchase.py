# Generated by Django 4.2rc1 on 2023-04-16 15:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0006_rename_type_payment_payment_type_and_more"),
        ("product", "0016_alter_stocktransaction_journal"),
    ]

    operations = [
        migrations.AlterField(
            model_name="stocklot",
            name="purchase",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="purchase.invoice",
            ),
        ),
    ]