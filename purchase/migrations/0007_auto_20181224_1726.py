# Generated by Django 2.1.3 on 2018-12-24 11:56

from django.db import migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('purchase', '0006_auto_20181224_1257'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from='id'),
        ),
    ]
