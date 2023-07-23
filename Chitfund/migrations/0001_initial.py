# Generated by Django 4.2.3 on 2023-07-23 10:51

import django.db.models.deletion
import django.utils.timezone
import django_extensions.db.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Allotment",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("amount", models.PositiveIntegerField()),
                ("installment", models.PositiveIntegerField()),
                (
                    "slug",
                    django_extensions.db.fields.AutoSlugField(
                        blank=True, editable=False, populate_from="to_member"
                    ),
                ),
                ("created", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "ordering": ("-created",),
            },
        ),
        migrations.CreateModel(
            name="Contact",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                (
                    "slug",
                    django_extensions.db.fields.AutoSlugField(
                        blank=True, editable=False, populate_from="name"
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("phoneno", models.CharField(max_length=10)),
            ],
            options={
                "ordering": ("-created",),
            },
        ),
        migrations.CreateModel(
            name="Collection",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "slug",
                    django_extensions.db.fields.AutoSlugField(
                        blank=True, editable=False, populate_from="member"
                    ),
                ),
                (
                    "date_collected",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("amount", models.PositiveIntegerField()),
                (
                    "allotment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="Chitfund.allotment",
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="Chitfund.contact",
                    ),
                ),
            ],
            options={
                "ordering": ("-pk",),
            },
        ),
        migrations.CreateModel(
            name="Chit",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                (
                    "slug",
                    django_extensions.db.fields.AutoSlugField(
                        blank=True, editable=False, populate_from="name"
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("type", models.CharField(max_length=30)),
                ("amount", models.PositiveIntegerField()),
                ("commission", models.PositiveIntegerField()),
                ("member_limit", models.PositiveSmallIntegerField()),
                ("date_to_allot", models.DateField()),
                (
                    "members",
                    models.ManyToManyField(
                        related_name="members", to="Chitfund.contact"
                    ),
                ),
                (
                    "owner",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="owner",
                        to="Chitfund.contact",
                    ),
                ),
            ],
            options={
                "ordering": ("-created",),
            },
        ),
        migrations.AddField(
            model_name="allotment",
            name="chit",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="Chitfund.chit"
            ),
        ),
        migrations.AddField(
            model_name="allotment",
            name="to_member",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="Chitfund.contact"
            ),
        ),
    ]
