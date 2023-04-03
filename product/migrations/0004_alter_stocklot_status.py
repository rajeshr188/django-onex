# Generated by Django 4.2rc1 on 2023-04-01 17:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0003_views"),
    ]

    operations = [
        migrations.AlterField(
            model_name="stocklot",
            name="status",
            field=models.CharField(
                choices=[
                    ("Empty", "Empty"),
                    ("Available", "Available"),
                    ("Sold", "Sold"),
                    ("Approval", "Approval"),
                    ("Return", "Return"),
                ],
                default="Empty",
                max_length=10,
            ),
        ),
    ]