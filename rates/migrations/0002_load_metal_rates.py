# Generated by Django 4.2.3 on 2024-02-16 08:25
from django.core.management import call_command
from django.db import migrations

def load_fixture(apps, schema_editor):
    call_command('loaddata', 'metal_rates.json')

class Migration(migrations.Migration):
    dependencies = [
        ("rates", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(load_fixture),
    ]