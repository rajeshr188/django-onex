# Generated by Django 3.2.5 on 2021-11-10 15:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dea', '0006_auto_20211110_1529'),
        ('product', '0005_auto_20211030_1147'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stocktransaction',
            name='journal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stxns', to='dea.journal'),
        ),
    ]