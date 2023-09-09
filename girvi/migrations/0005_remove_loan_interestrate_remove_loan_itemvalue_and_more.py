# Generated by Django 4.2.3 on 2023-08-20 04:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0004_auto_views"),
        ("girvi", "0004_alter_loan_loanamount_alter_loanitem_interest"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="loan",
            name="interestrate",
        ),
        migrations.RemoveField(
            model_name="loan",
            name="itemvalue",
        ),
        migrations.RemoveField(
            model_name="loan",
            name="itemweight",
        ),
        migrations.AlterField(
            model_name="loan",
            name="itemtype",
            field=models.CharField(
                choices=[
                    ("Gold", "Gold"),
                    ("Silver", "Silver"),
                    ("Bronze", "Bronze"),
                    ("Mixed", "Mixed"),
                ],
                default="Gold",
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="loan",
            name="loanamount",
            field=models.PositiveIntegerField(
                blank=True, default=0, null=True, verbose_name="Amount"
            ),
        ),
        migrations.AlterField(
            model_name="loanitem",
            name="interest",
            field=models.DecimalField(
                blank=True, decimal_places=2, default=0, max_digits=10, null=True
            ),
        ),
        migrations.AlterField(
            model_name="loanitem",
            name="item",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="product.productvariant",
            ),
        ),
        migrations.AlterField(
            model_name="loanitem",
            name="quantity",
            field=models.PositiveIntegerField(default=1),
        ),
    ]
