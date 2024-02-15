# Generated by Django 4.2.3 on 2024-02-15 10:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contact", "0001_initial"),
        ("product", "0002_initial"),
        ("approval", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="return",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="approvalline",
            name="approval",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="items",
                to="approval.approval",
            ),
        ),
        migrations.AddField(
            model_name="approvalline",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="lineitems",
                to="product.stocklot",
            ),
        ),
        migrations.AddField(
            model_name="approval",
            name="contact",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="contact",
                to="contact.customer",
            ),
        ),
        migrations.AddField(
            model_name="approval",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
