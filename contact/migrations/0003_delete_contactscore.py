# Generated by Django 4.2.3 on 2023-09-04 10:54

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("contact", "0002_initial"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ContactScore",
        ),
    ]
