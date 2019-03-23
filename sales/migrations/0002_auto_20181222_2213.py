# Generated by Django 2.1.3 on 2018-12-22 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='status',
            field=models.CharField(choices=[('Draft', 'Draft'), ('Paid', 'Paid'), ('Partially Paid', 'partiallyPaid'), ('Unpaid', 'Unpaid')], default='Unpaid', max_length=10),
        ),
    ]