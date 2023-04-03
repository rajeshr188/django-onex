# Generated by Django 4.2rc1 on 2023-03-31 09:06

from django.core.management import call_command
from django.db import migrations


def load_fixture(apps, schema_editor):
    call_command("loaddata", "invoice/fixtures/data.json")


class Migration(migrations.Migration):
    dependencies = [
        ("invoice", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(load_fixture),
    ]
