# Generated by Django 4.2.3 on 2024-01-29 13:44

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
        ("dea", "0003_views"),
    ]

    operations = [
        migrations.CreateModel(
            name="JournalEntry",
            fields=[
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("desc", models.TextField(blank=True, null=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
            ],
            options={
                "get_latest_by": "id",
            },
        ),
        migrations.AlterModelOptions(
            name="journal",
            options={"get_latest_by": "created_at"},
        ),
        migrations.RemoveIndex(
            model_name="journal",
            name="dea_journal_content_6aff51_idx",
        ),
        migrations.RenameField(
            model_name="journal",
            old_name="created",
            new_name="created_at",
        ),
        migrations.RenameField(
            model_name="journal",
            old_name="updated",
            new_name="updated_at",
        ),
        migrations.RemoveField(
            model_name="accounttransaction",
            name="journal",
        ),
        migrations.RemoveField(
            model_name="journal",
            name="content_type",
        ),
        migrations.RemoveField(
            model_name="journal",
            name="journal_type",
        ),
        migrations.RemoveField(
            model_name="journal",
            name="object_id",
        ),
        migrations.RemoveField(
            model_name="ledgertransaction",
            name="journal",
        ),
        migrations.AddField(
            model_name="journal",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="journal",
            name="polymorphic_ctype",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="polymorphic_%(app_label)s.%(class)s_set+",
                to="contenttypes.contenttype",
            ),
        ),
        migrations.AddField(
            model_name="journal",
            name="posted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="journal",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name="journalentry",
            name="journal",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="journal_entries",
                to="dea.journal",
            ),
        ),
        migrations.AddField(
            model_name="accounttransaction",
            name="journal_entry",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="atxns",
                to="dea.journalentry",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="ledgertransaction",
            name="journal_entry",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="ltxns",
                to="dea.journalentry",
            ),
            preserve_default=False,
        ),
    ]
