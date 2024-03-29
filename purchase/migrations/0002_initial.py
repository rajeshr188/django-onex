# Generated by Django 4.2.3 on 2024-02-15 10:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("purchase", "0001_initial"),
        ("invoice", "0001_initial"),
        ("product", "0002_initial"),
        ("contact", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="payment",
            name="invoices",
            field=models.ManyToManyField(
                through="purchase.PaymentAllocation", to="purchase.invoice"
            ),
        ),
        migrations.AddField(
            model_name="payment",
            name="supplier",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="payments",
                to="contact.customer",
                verbose_name="Supplier",
            ),
        ),
        migrations.AddField(
            model_name="invoiceitem",
            name="invoice",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="purchase_items",
                to="purchase.invoice",
            ),
        ),
        migrations.AddField(
            model_name="invoiceitem",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="products",
                to="product.productvariant",
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="purchases_created",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="supplier",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="purchases",
                to="contact.customer",
                verbose_name="Supplier",
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="term",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="purchase_term",
                to="invoice.paymentterm",
            ),
        ),
    ]
