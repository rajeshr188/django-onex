# Generated by Django 4.2.3 on 2023-08-21 04:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("girvi", "0008_remove_loan_itemtype"),
    ]

    operations = [
        migrations.AddField(
            model_name="loan",
            name="interestrate",
            field=models.PositiveSmallIntegerField(
                blank=True, default=2, null=True, verbose_name="ROI"
            ),
        ),
        migrations.AddField(
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
        migrations.AddField(
            model_name="loan",
            name="itemweight",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=0,
                max_digits=10,
                null=True,
                verbose_name="Weight",
            ),
        ),
    ]
