# Generated by Django 2.1.3 on 2019-02-15 05:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0003_auto_20190215_0944'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='slug',
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='slug',
        ),
    ]
