# Generated by Django 4.1.5 on 2023-02-27 11:09

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("contact", "0007_alter_contact_number"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="customer",
            name="phonenumber",
        ),
    ]
