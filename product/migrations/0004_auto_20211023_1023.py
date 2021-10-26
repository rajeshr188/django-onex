# Generated by Django 3.2.5 on 2021-10-23 10:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0003_alter_producttype_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockBatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('qty', models.IntegerField(default=0)),
                ('wt', models.DecimalField(decimal_places=3, max_digits=10)),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.stock')),
            ],
        ),
        migrations.AddField(
            model_name='stocktransaction',
            name='stock_batch',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='product.stockbatch'),
        ),
    ]
