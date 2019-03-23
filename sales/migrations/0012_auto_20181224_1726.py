# Generated by Django 2.1.3 on 2018-12-24 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0011_auto_20181223_1823'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='status',
            field=models.CharField(choices=[('Draft', 'Draft'), ('Paid', 'Paid'), ('Partially Paid', 'PartiallyPaid'), ('Unpaid', 'Unpaid')], default='Unpaid', max_length=15),
        ),
    ]