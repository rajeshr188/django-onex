# Generated by Django 4.2.3 on 2024-01-29 13:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("dea", "0004_journalentry_alter_journal_options_and_more"),
        ("girvi", "0017_alter_loan_loanid"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="adjustment",
            options={"ordering": ("created_at",)},
        ),
        migrations.RenameField(
            model_name="adjustment",
            old_name="loan",
            new_name="adj_loan",
        ),
        migrations.RenameField(
            model_name="release",
            old_name="loan",
            new_name="release_loan",
        ),
        migrations.RemoveField(
            model_name="adjustment",
            name="created",
        ),
        migrations.RemoveField(
            model_name="adjustment",
            name="created_by",
        ),
        migrations.RemoveField(
            model_name="adjustment",
            name="id",
        ),
        migrations.RemoveField(
            model_name="loan",
            name="created",
        ),
        migrations.RemoveField(
            model_name="loan",
            name="created_by",
        ),
        migrations.RemoveField(
            model_name="loan",
            name="id",
        ),
        migrations.RemoveField(
            model_name="loan",
            name="updated",
        ),
        migrations.RemoveField(
            model_name="release",
            name="created",
        ),
        migrations.RemoveField(
            model_name="release",
            name="created_by",
        ),
        migrations.RemoveField(
            model_name="release",
            name="id",
        ),
        migrations.RemoveField(
            model_name="release",
            name="updated",
        ),
        migrations.AddField(
            model_name="adjustment",
            name="journal_ptr",
            field=models.OneToOneField(
                auto_created=True,
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                parent_link=True,
                primary_key=True,
                serialize=False,
                to="dea.journal",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="loan",
            name="journal_ptr",
            field=models.OneToOneField(
                auto_created=True,
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                parent_link=True,
                primary_key=True,
                serialize=False,
                to="dea.journal",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="release",
            name="journal_ptr",
            field=models.OneToOneField(
                auto_created=True,
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                parent_link=True,
                primary_key=True,
                serialize=False,
                to="dea.journal",
            ),
            preserve_default=False,
        ),
    ]