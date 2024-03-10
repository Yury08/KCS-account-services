# Generated by Django 4.2.7 on 2024-03-07 10:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="account",
            name="token",
            field=models.CharField(
                default="972fca40-7949-4e5f-8607-3bb3096b42e9", max_length=255
            ),
        ),
        migrations.CreateModel(
            name="BlackListedToken",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("token", models.CharField(max_length=500)),
                ("timestamp", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="token_user",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("token", "user")},
            },
        ),
    ]
