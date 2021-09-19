# Generated by Django 3.2.5 on 2021-09-19 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Approval',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('total_wt', models.DecimalField(decimal_places=3, default=0, max_digits=10)),
                ('total_qty', models.IntegerField(default=0)),
                ('posted', models.BooleanField(default=False)),
                ('is_billed', models.BooleanField(default=False)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Complete', 'Complete')], default='Pending', max_length=10)),
            ],
            options={
                'ordering': ('created_at',),
            },
        ),
        migrations.CreateModel(
            name='ApprovalLine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(default=0)),
                ('weight', models.DecimalField(decimal_places=3, default=0.0, max_digits=10)),
                ('touch', models.DecimalField(decimal_places=3, default=0.0, max_digits=10)),
                ('status', models.CharField(blank=True, choices=[('Pending', 'Pending'), ('Returned', 'Returned'), ('Billed', 'Billed')], default='Pending', max_length=30)),
            ],
            options={
                'ordering': ('approval',),
            },
        ),
        migrations.CreateModel(
            name='ApprovalLineReturn',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('quantity', models.IntegerField(default=0)),
                ('weight', models.DecimalField(decimal_places=3, default=0.0, max_digits=10)),
                ('posted', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('id',),
            },
        ),
    ]
