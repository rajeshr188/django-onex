# Generated by Django 2.2.9 on 2020-03-26 07:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0010_auto_20200326_1127'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stree',
            name='barcode',
            field=models.CharField(default='1', max_length=20, null=True),
        ),
    ]