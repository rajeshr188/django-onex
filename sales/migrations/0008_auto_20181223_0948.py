# Generated by Django 2.1.3 on 2018-12-23 04:18

from django.db import migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0007_auto_20181223_0945'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receiptline',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from='id'),
        ),
    ]