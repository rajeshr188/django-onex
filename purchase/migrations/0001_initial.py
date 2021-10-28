# Generated by Django 3.2.5 on 2021-10-27 16:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0002_delete_voucher'),
        ('invoice', '0001_initial'),
        ('product', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contact', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated', models.DateTimeField(auto_now_add=True)),
                ('rate', models.DecimalField(decimal_places=3, default=0, max_digits=10)),
                ('is_gst', models.BooleanField(default=False)),
                ('posted', models.BooleanField(default=False)),
                ('gross_wt', models.DecimalField(decimal_places=4, default=0.0, max_digits=14)),
                ('net_wt', models.DecimalField(decimal_places=4, default=0.0, max_digits=14)),
                ('total', models.DecimalField(decimal_places=4, default=0.0, max_digits=14)),
                ('discount', models.DecimalField(decimal_places=4, default=0.0, max_digits=14)),
                ('balance', models.DecimalField(decimal_places=4, default=0.0, max_digits=14)),
                ('status', models.CharField(choices=[('Paid', 'Paid'), ('PartiallyPaid', 'PartiallyPaid'), ('Unpaid', 'Unpaid')], default='Unpaid', max_length=15)),
                ('balancetype', models.CharField(choices=[('INR', 'Cash'), ('USD', 'Gold'), ('AUD', 'Silver')], default='INR', max_length=30)),
                ('metaltype', models.CharField(choices=[('Gold', 'Gold'), ('Silver', 'Silver')], default='Gold', max_length=30)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='purchased', to=settings.AUTH_USER_MODEL)),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchases', to='contact.customer')),
                ('term', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='purchase_term', to='invoice.paymentterm')),
            ],
            options={
                'ordering': ('id', 'created'),
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated', models.DateTimeField(auto_now_add=True)),
                ('type', models.CharField(choices=[('INR', 'Cash'), ('USD', 'Gold'), ('AUD', 'Silver')], default='INR', max_length=30, verbose_name='Currency')),
                ('rate', models.IntegerField(default=0)),
                ('total', models.DecimalField(decimal_places=3, max_digits=10)),
                ('description', models.TextField(max_length=100)),
                ('status', models.CharField(choices=[('Allotted', 'Allotted'), ('Partially Allotted', 'PartiallyAllotted'), ('Unallotted', 'Unallotted')], default='Unallotted', max_length=18)),
                ('posted', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='contact.customer')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='PaymentLine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('amount', models.DecimalField(decimal_places=3, max_digits=10)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='purchase.invoice')),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='purchase.payment')),
            ],
        ),
        migrations.CreateModel(
            name='PaymentItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.DecimalField(blank=True, decimal_places=3, default=0.0, max_digits=10)),
                ('touch', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10)),
                ('nettwt', models.DecimalField(blank=True, decimal_places=3, default=0.0, max_digits=10)),
                ('rate', models.IntegerField(default=0)),
                ('amount', models.DecimalField(decimal_places=3, max_digits=10)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='purchase.payment')),
            ],
        ),
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('huid', models.CharField(blank=True, max_length=6, null=True, unique=True)),
                ('quantity', models.IntegerField()),
                ('weight', models.DecimalField(decimal_places=3, max_digits=10)),
                ('touch', models.DecimalField(decimal_places=3, max_digits=10)),
                ('net_wt', models.DecimalField(decimal_places=3, default=0, max_digits=10)),
                ('total', models.DecimalField(decimal_places=3, max_digits=10)),
                ('is_return', models.BooleanField(default=False, verbose_name='Return')),
                ('makingcharge', models.DecimalField(blank=True, decimal_places=3, max_digits=10, verbose_name='mc')),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchaseitems', to='purchase.invoice')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='product.productvariant')),
            ],
            options={
                'ordering': ('-pk',),
            },
        ),
    ]
