# Generated by Django 3.2.5 on 2021-11-17 07:39

import django.contrib.postgres.fields.hstore
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import mptt.fields
import versatileimagefield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dea', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from='name')),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from='name')),
                ('description', models.TextField(blank=True)),
                ('background_image', versatileimagefield.fields.VersatileImageField(blank=True, null=True, upload_to='category-backgrounds')),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='product.category')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True)),
                ('description', models.TextField()),
                ('attributes', django.contrib.postgres.fields.hstore.HStoreField(blank=True, default=dict)),
                ('jattributes', models.JSONField(blank=True, default=dict, null=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='product.category')),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', versatileimagefield.fields.VersatileImageField(upload_to='product/')),
                ('ppoi', versatileimagefield.fields.PPOIField(default='0.5x0.5', editable=False, max_length=20, verbose_name='Image PPOI')),
                ('alt', models.CharField(blank=True, max_length=128)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='product.product')),
            ],
            options={
                'ordering': ('-id',),
            },
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sku', models.CharField(max_length=32, unique=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('product_code', models.CharField(max_length=32, unique=True)),
                ('attributes', django.contrib.postgres.fields.hstore.HStoreField(blank=True, default=dict)),
                ('jattributes', models.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('reorderat', models.IntegerField(default=1)),
                ('barcode', models.CharField(blank=True, editable=False, max_length=6, null=True, unique=True)),
                ('huid', models.CharField(blank=True, max_length=6, null=True, unique=True)),
                ('melting', models.DecimalField(decimal_places=3, default=100, max_digits=10)),
                ('cost', models.DecimalField(decimal_places=3, default=100, max_digits=10)),
                ('touch', models.DecimalField(decimal_places=3, default=0, max_digits=10)),
                ('wastage', models.DecimalField(decimal_places=3, default=0, max_digits=10)),
                ('tracking_type', models.CharField(choices=[('Lot', 'Lot'), ('Unique', 'Unique')], default='Lot', max_length=10, null=True, verbose_name='track_by')),
                ('status', models.CharField(choices=[('Empty', 'Empty'), ('Available', 'Available'), ('Sold', 'Sold'), ('Approval', 'Approval'), ('Return', 'Return'), ('Merged', 'Merged')], default='Empty', max_length=10)),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.productvariant')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='VariantImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variant_images', to='product.productimage')),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variant_images', to='product.productvariant')),
            ],
        ),
        migrations.CreateModel(
            name='StockTransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('quantity', models.IntegerField(default=0)),
                ('weight', models.DecimalField(decimal_places=3, default=0, max_digits=10)),
                ('description', models.TextField()),
                ('activity_type', models.CharField(choices=[('P', 'Purchase'), ('PR', 'Purchase Return'), ('S', 'Sales'), ('SR', 'Sales Return'), ('A', 'Approval'), ('AR', 'Approval Return'), ('RM', 'Remove'), ('AD', 'Add')], default='PURCHASE', max_length=20)),
                ('journal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stxns', to='dea.journal')),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.stock')),
            ],
            options={
                'ordering': ('-created',),
                'get_latest_by': ['created'],
            },
        ),
        migrations.CreateModel(
            name='StockStatement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method', models.CharField(choices=[('Auto', 'Auto'), ('Physical', 'Physical')], default='Auto', max_length=20)),
                ('created', models.DateTimeField(auto_now=True)),
                ('Closing_wt', models.DecimalField(decimal_places=3, max_digits=14)),
                ('Closing_qty', models.IntegerField()),
                ('total_wt_in', models.DecimalField(decimal_places=3, default=0.0, max_digits=14)),
                ('total_wt_out', models.DecimalField(decimal_places=3, default=0.0, max_digits=14)),
                ('total_qty_in', models.IntegerField(default=0.0)),
                ('total_qty_out', models.IntegerField(default=0.0)),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.stock')),
            ],
            options={
                'ordering': ('created',),
                'get_latest_by': ['created'],
            },
        ),
        migrations.AddField(
            model_name='productvariant',
            name='images',
            field=models.ManyToManyField(through='product.VariantImage', to='product.ProductImage'),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='product.product'),
        ),
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('has_variants', models.BooleanField(default=True)),
                ('product_attributes', models.ManyToManyField(blank=True, related_name='product_types', to='product.Attribute')),
                ('variant_attributes', models.ManyToManyField(blank=True, related_name='product_variant_types', to='product.Attribute')),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.AddField(
            model_name='product',
            name='product_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='product.producttype'),
        ),
        migrations.CreateModel(
            name='AttributeValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('value', models.CharField(default='', max_length=100)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from='name')),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='product.attribute')),
            ],
            options={
                'ordering': ('-id',),
                'unique_together': {('name', 'attribute')},
            },
        ),
    ]
