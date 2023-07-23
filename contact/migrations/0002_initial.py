# Generated by Django 4.2.3 on 2023-07-23 10:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contact", "0001_initial"),
        ("product", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="customer",
            name="pricing_tier",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="product.pricingtier",
            ),
        ),
        migrations.AddField(
            model_name="contactscore",
            name="contact",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="contact.customer"
            ),
        ),
        migrations.AddField(
            model_name="contact",
            name="customer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="contactno",
                to="contact.customer",
            ),
        ),
        migrations.AddField(
            model_name="address",
            name="Customer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="address",
                to="contact.customer",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="customer",
            unique_together={("name", "relatedas", "relatedto")},
        ),
    ]
