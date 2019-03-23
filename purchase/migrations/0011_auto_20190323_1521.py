# Generated by Django 2.1.7 on 2019-03-23 09:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchase', '0010_auto_20190215_1036'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='status',
            field=models.CharField(choices=[('Allotted', 'Allotted'), ('Partially Allotted', 'PartiallyAllotted'), ('Unallotted', 'Unallotted')], default='Unallotted', max_length=15),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='status',
            field=models.CharField(choices=[('Paid', 'Paid'), ('PartiallyPaid', 'PartiallyPaid'), ('Unpaid', 'Unpaid')], default='Unpaid', max_length=15),
        ),
    ]
