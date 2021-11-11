# Generated by Django 3.2.5 on 2021-10-30 11:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0004_alter_stocktransaction_movement_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockbatch',
            name='cost',
            field=models.DecimalField(decimal_places=3, default=100, max_digits=14),
        ),
        migrations.AlterField(
            model_name='stockbatch',
            name='weight',
            field=models.DecimalField(decimal_places=3, max_digits=14),
        ),
    ]