# Generated by Django 4.1.5 on 2023-03-11 10:52

import phonenumber_field.modelfields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("contact", "0010_remove_customer_type_customer_customer_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="contact",
            name="phone_number",
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True, max_length=128, region=None
            ),
        ),
    ]
