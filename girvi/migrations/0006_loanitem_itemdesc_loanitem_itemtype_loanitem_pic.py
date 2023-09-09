# Generated by Django 4.2.3 on 2023-08-20 04:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("girvi", "0005_remove_loan_interestrate_remove_loan_itemvalue_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="loanitem",
            name="itemdesc",
            field=models.TextField(
                blank=True, max_length=100, null=True, verbose_name="Item"
            ),
        ),
        migrations.AddField(
            model_name="loanitem",
            name="itemtype",
            field=models.CharField(
                choices=[("Gold", "Gold"), ("Silver", "Silver"), ("Bronze", "Bronze")],
                default="Gold",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="loanitem",
            name="pic",
            field=models.ImageField(blank=True, null=True, upload_to="loan_pics/"),
        ),
    ]
