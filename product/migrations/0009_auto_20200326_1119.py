# Generated by Django 2.2.9 on 2020-03-26 05:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0008_auto_20200326_1118'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stree',
            name='barcode',
            field=models.CharField(default='1', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='stree',
            name='cost',
            field=models.DecimalField(decimal_places=3, default=75, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='stree',
            name='weight',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10, null=True),
        ),
    ]
