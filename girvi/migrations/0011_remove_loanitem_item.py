# Generated by Django 4.2.3 on 2023-08-21 05:37

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("girvi", "0010_remove_loan_interestrate"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="loanitem",
            name="item",
        ),
    ]
