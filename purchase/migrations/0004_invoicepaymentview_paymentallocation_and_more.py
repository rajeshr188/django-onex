# Generated by Django 4.2rc1 on 2023-04-07 06:47

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0003_alter_invoiceitem_total"),
    ]

    operations = [
        migrations.CreateModel(
            name="InvoicePaymentView",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("invoice_number", models.CharField(max_length=50)),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "amount_paid",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "amount_allocated",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
            ],
            options={
                "db_table": "invoice_payment_view",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="PaymentAllocation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "last_updated",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "allocated_amount",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="purchase.invoice",
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="paymentline",
            name="invoice",
        ),
        migrations.RemoveField(
            model_name="paymentline",
            name="payment",
        ),
        migrations.AddField(
            model_name="payment",
            name="touch",
            field=models.DecimalField(decimal_places=3, default=100, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="payment",
            name="weight",
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name="PaymentItem",
        ),
        migrations.DeleteModel(
            name="PaymentLine",
        ),
        migrations.AddField(
            model_name="paymentallocation",
            name="payment",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="purchase.payment"
            ),
        ),
        migrations.AddField(
            model_name="payment",
            name="invoices",
            field=models.ManyToManyField(
                through="purchase.PaymentAllocation", to="purchase.invoice"
            ),
        ),
    ]
