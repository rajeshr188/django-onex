# Generated by Django 4.2rc1 on 2023-04-16 07:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dea", "0008_alter_journal_content_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="journal",
            name="object_id",
            field=models.PositiveIntegerField(),
        ),
        migrations.AddIndex(
            model_name="journal",
            index=models.Index(
                fields=["content_type", "object_id"],
                name="dea_journal_content_6aff51_idx",
            ),
        ),
    ]