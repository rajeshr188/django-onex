# Generated by Django 2.1.3 on 2019-02-13 04:51

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0014_auto_20190102_1714'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='created',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now),
        ),
    ]
