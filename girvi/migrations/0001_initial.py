# Generated by Django 2.1.3 on 2018-11-30 07:24

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_extensions.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contact', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from='name')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('type', models.CharField(choices=[('PBL', 'Pawn Brokers License'), ('GST', 'Goods & Service Tax')], default='PBL', max_length=30)),
                ('shopname', models.CharField(max_length=30)),
                ('address', models.TextField(max_length=100)),
                ('phonenumber', models.CharField(max_length=30)),
                ('propreitor', models.CharField(max_length=30)),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='Loan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loanid', models.CharField(max_length=255)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from='loanid')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('itemtype', models.CharField(choices=[('Gold', 'Gold'), ('Silver', 'Silver'), ('Bronze', 'Bronze'), ('O', 'Other')], default='Gold', max_length=30)),
                ('itemdesc', models.TextField(max_length=30)),
                ('itemweight', models.DecimalField(decimal_places=2, max_digits=10)),
                ('itemvalue', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('loanamount', models.PositiveIntegerField()),
                ('interestrate', models.PositiveSmallIntegerField()),
                ('interest', models.PositiveIntegerField()),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contact.Customer')),
                ('license', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='girvi.License')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='Release',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('releaseid', models.CharField(max_length=255)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from='releaseid')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('interestpaid', models.IntegerField()),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='releasedby', to='contact.Customer')),
                ('loan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='release', to='girvi.Loan')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
    ]
