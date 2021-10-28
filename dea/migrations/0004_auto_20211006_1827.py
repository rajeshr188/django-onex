# Generated by Django 3.2.5 on 2021-10-28 09:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dea', '0003_dea_views'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='accounttransaction',
            index=models.Index(fields=['ledgerno'], name='dea_account_ledgern_eea025_idx'),
        ),
        migrations.AddIndex(
            model_name='ledgertransaction',
            index=models.Index(fields=['ledgerno'], name='dea_ledgert_ledgern_b79320_idx'),
        ),
        migrations.AddIndex(
            model_name='ledgertransaction',
            index=models.Index(fields=['ledgerno_dr'], name='dea_ledgert_ledgern_31d496_idx'),
        ),
        migrations.AlterField(
            model_name='journal',
            name='type',
            field=models.CharField(choices=[('Base Journal', 'base journal'), ('Loan Taken', 'Loan taken'), ('Loan Given', 'Loan given'), ('Loan Released', 'Loan released'), ('Loan Paid', 'Loan paid'), ('Interest Paid', 'Interest Paid'), ('Interest Received', 'Interest Received'), ('Sales', 'Sales'), ('Sales Return', 'Sales Return'), ('Receipt', 'Receipt'), ('Purchase', 'Purchase'), ('Purchase Return', 'Purchase Return'), ('Payment', 'Payment'), ('Stock', 'Stock')], default='Base Journal', max_length=50),
        ),
    ]
