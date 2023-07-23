# Generated by Django 4.2.3 on 2023-07-23 00:39
from django.contrib.postgres.operations import HStoreExtension

import django.contrib.postgres.fields.hstore
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("dea", "0001_initial"),
    ]

    operations = [
        HStoreExtension(),
        migrations.CreateModel(
            name="Attribute",
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
                ("name", models.CharField(max_length=50)),
                (
                    "slug",
                    django_extensions.db.fields.AutoSlugField(
                        blank=True, editable=False, populate_from="name"
                    ),
                ),
            ],
            options={
                "ordering": ("id",),
            },
        ),
        migrations.CreateModel(
            name="AttributeValue",
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
                ("name", models.CharField(max_length=100)),
                ("value", models.CharField(default="", max_length=100)),
                (
                    "slug",
                    django_extensions.db.fields.AutoSlugField(
                        blank=True, editable=False, populate_from="name"
                    ),
                ),
            ],
            options={
                "ordering": ("-id",),
            },
        ),
        migrations.CreateModel(
            name="Category",
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
                ("name", models.CharField(max_length=128, unique=True)),
                (
                    "slug",
                    django_extensions.db.fields.AutoSlugField(
                        blank=True, editable=False, populate_from="name"
                    ),
                ),
                ("description", models.TextField(blank=True)),
                (
                    "background_image",
                    models.ImageField(
                        blank=True, null=True, upload_to="category-backgrounds"
                    ),
                ),
                ("lft", models.PositiveIntegerField(editable=False)),
                ("rght", models.PositiveIntegerField(editable=False)),
                ("tree_id", models.PositiveIntegerField(db_index=True, editable=False)),
                ("level", models.PositiveIntegerField(editable=False)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Movement",
            fields=[
                (
                    "id",
                    models.CharField(max_length=3, primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=30)),
                ("direction", models.CharField(default="+", max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name="Price",
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
                (
                    "purchase_price",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                ("selling_price", models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name="PricingTier",
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
                ("name", models.CharField(max_length=128, unique=True)),
                ("description", models.TextField(blank=True)),
                ("minimum_quantity", models.PositiveIntegerField()),
                ("lft", models.PositiveIntegerField(editable=False)),
                ("rght", models.PositiveIntegerField(editable=False)),
                ("tree_id", models.PositiveIntegerField(db_index=True, editable=False)),
                ("level", models.PositiveIntegerField(editable=False)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="PricingTierProductPrice",
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
                (
                    "purchase_price",
                    models.DecimalField(decimal_places=3, max_digits=13),
                ),
                ("selling_price", models.DecimalField(decimal_places=3, max_digits=13)),
            ],
        ),
        migrations.CreateModel(
            name="Product",
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
                ("name", models.CharField(max_length=128, unique=True)),
                ("description", models.TextField()),
                (
                    "attributes",
                    django.contrib.postgres.fields.hstore.HStoreField(
                        blank=True, default=dict
                    ),
                ),
                ("jattributes", models.JSONField(blank=True, default=dict, null=True)),
            ],
            options={
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="ProductImage",
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
                ("image", models.ImageField(upload_to="product/")),
                ("alt", models.CharField(blank=True, max_length=128)),
            ],
            options={
                "ordering": ("-id",),
            },
        ),
        migrations.CreateModel(
            name="ProductType",
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
                ("name", models.CharField(max_length=128)),
                ("has_variants", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="ProductVariant",
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
                ("sku", models.CharField(max_length=32, unique=True)),
                ("name", models.CharField(max_length=255, unique=True)),
                ("product_code", models.CharField(max_length=32, unique=True)),
                (
                    "attributes",
                    django.contrib.postgres.fields.hstore.HStoreField(
                        blank=True, default=dict
                    ),
                ),
                ("jattributes", models.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name="Rate",
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
                (
                    "metal",
                    models.CharField(
                        choices=[("Gold", "Gold"), ("Silver", "Silver")],
                        default="Gold",
                        max_length=6,
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        choices=[("INR", "INR"), ("USD", "USD")],
                        default="INR",
                        max_length=3,
                    ),
                ),
                (
                    "purity",
                    models.CharField(
                        choices=[
                            ("24k", "24K"),
                            ("22k", "22K"),
                            ("18k", "18K"),
                            ("14k", "14K"),
                            ("10k", "10K"),
                        ],
                        default="24k",
                        max_length=3,
                    ),
                ),
                ("buying_rate", models.DecimalField(decimal_places=2, max_digits=10)),
                ("selling_rate", models.DecimalField(decimal_places=2, max_digits=10)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="RateSource",
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
                ("name", models.CharField(max_length=30)),
                ("location", models.CharField(max_length=30)),
                ("tax_included", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="Stock",
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
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                ("reorderat", models.IntegerField(default=1)),
            ],
            options={
                "ordering": ("-created",),
            },
        ),
        migrations.CreateModel(
            name="StockLot",
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
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                ("quantity", models.IntegerField(default=0)),
                ("weight", models.DecimalField(decimal_places=3, max_digits=10)),
                (
                    "barcode",
                    models.CharField(
                        blank=True,
                        editable=False,
                        max_length=155,
                        null=True,
                        unique=True,
                    ),
                ),
                (
                    "huid",
                    models.CharField(blank=True, max_length=6, null=True, unique=True),
                ),
                ("stock_code", models.CharField(blank=True, max_length=4, null=True)),
                (
                    "purchase_touch",
                    models.DecimalField(decimal_places=3, max_digits=10),
                ),
                (
                    "purchase_rate",
                    models.DecimalField(
                        blank=True, decimal_places=3, max_digits=10, null=True
                    ),
                ),
                ("is_unique", models.BooleanField(default=False)),
                (
                    "status",
                    models.CharField(
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
            ],
        ),
        migrations.CreateModel(
            name="StockBalance",
            fields=[
                (
                    "stock",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        primary_key=True,
                        serialize=False,
                        to="product.stock",
                    ),
                ),
                ("Closing_wt", models.DecimalField(decimal_places=3, max_digits=14)),
                ("Closing_qty", models.IntegerField()),
                ("in_wt", models.DecimalField(decimal_places=3, max_digits=14)),
                ("in_qty", models.IntegerField()),
                ("out_wt", models.DecimalField(decimal_places=3, max_digits=14)),
                ("out_qty", models.IntegerField()),
            ],
            options={
                "db_table": "stock_balance",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="StockLotBalance",
            fields=[
                (
                    "lot",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        primary_key=True,
                        serialize=False,
                        to="product.stocklot",
                    ),
                ),
                ("Closing_wt", models.DecimalField(decimal_places=3, max_digits=14)),
                ("Closing_qty", models.IntegerField()),
                (
                    "in_wt",
                    models.DecimalField(decimal_places=3, default=0.0, max_digits=14),
                ),
                ("in_qty", models.IntegerField(default=0)),
                (
                    "out_wt",
                    models.DecimalField(decimal_places=3, default=0.0, max_digits=14),
                ),
                ("out_qty", models.IntegerField(default=0)),
            ],
            options={
                "db_table": "stockbatch_balance",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="VariantImage",
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
                (
                    "image",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="variant_images",
                        to="product.productimage",
                    ),
                ),
                (
                    "variant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="variant_images",
                        to="product.productvariant",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="StockTransaction",
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
                ("created", models.DateTimeField(auto_now_add=True)),
                ("quantity", models.IntegerField(default=0)),
                (
                    "weight",
                    models.DecimalField(decimal_places=3, default=0, max_digits=10),
                ),
                ("description", models.TextField()),
                (
                    "journal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stxns",
                        to="dea.journal",
                    ),
                ),
                (
                    "lot",
                    models.ForeignKey(
                        default=1,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="product.stocklot",
                    ),
                ),
                (
                    "movement_type",
                    models.ForeignKey(
                        default="P",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="product.movement",
                    ),
                ),
                (
                    "stock",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="product.stock"
                    ),
                ),
            ],
            options={
                "ordering": ("-created",),
                "get_latest_by": ["created"],
            },
        ),
        migrations.CreateModel(
            name="StockStatement",
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
                (
                    "method",
                    models.CharField(
                        choices=[("Auto", "Auto"), ("Physical", "Physical")],
                        default="Auto",
                        max_length=20,
                    ),
                ),
                ("created", models.DateTimeField(auto_now=True)),
                ("Closing_wt", models.DecimalField(decimal_places=3, max_digits=14)),
                ("Closing_qty", models.IntegerField()),
                (
                    "total_wt_in",
                    models.DecimalField(decimal_places=3, default=0.0, max_digits=14),
                ),
                (
                    "total_wt_out",
                    models.DecimalField(decimal_places=3, default=0.0, max_digits=14),
                ),
                ("total_qty_in", models.IntegerField(default=0.0)),
                ("total_qty_out", models.IntegerField(default=0.0)),
                (
                    "lot",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="product.stocklot",
                    ),
                ),
                (
                    "stock",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="product.stock"
                    ),
                ),
            ],
            options={
                "ordering": ("created",),
                "get_latest_by": ["created"],
            },
        ),
    ]
