# Generated by Django 2.1.3 on 2019-02-04 04:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('girvi', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loan',
            name='loanid',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]