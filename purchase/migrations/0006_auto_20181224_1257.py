# Generated by Django 2.1.3 on 2018-12-24 07:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchase', '0005_auto_20181224_1256'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='balance',
            field=models.DecimalField(decimal_places=3, max_digits=10),
        ),
    ]