# Generated by Django 4.2rc1 on 2023-04-16 05:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("girvi", "0006_rename_qty_loanitem_quantity_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="loan",
            name="itemdesc",
            field=models.TextField(
                blank=True, max_length=100, null=True, verbose_name="Description"
            ),
        ),
        migrations.AlterField(
            model_name="loan",
            name="itemweight",
            field=models.DecimalField(
                decimal_places=2, max_digits=10, verbose_name="Weight"
            ),
        ),
    ]
