# Generated by Django 2.1.7 on 2019-03-29 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('girvi', '0007_auto_20190215_1036'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loan',
            name='itemtype',
            field=models.CharField(choices=[('Gold', 'Gold'), ('Silver', 'Silver'), ('Bronze', 'Bronze')], default='Gold', max_length=30),
        ),
    ]