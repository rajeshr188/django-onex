# Generated by Django 2.1.3 on 2018-12-22 17:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0003_auto_20181222_2257'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReceiptLine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=3, max_digits=10)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales.Invoice')),
            ],
        ),
        migrations.AlterField(
            model_name='receipt',
            name='type',
            field=models.CharField(choices=[('Cash', 'Cash'), ('Metal', 'Metal')], default='Cash', max_length=30, verbose_name='Currency'),
        ),
        migrations.AddField(
            model_name='receiptline',
            name='receipt',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales.Receipt'),
        ),
    ]