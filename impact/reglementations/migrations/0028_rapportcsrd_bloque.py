# Generated by Django 5.1.5 on 2025-01-17 14:15
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("reglementations", "0027_rapportcsrd_lien_rapport"),
    ]

    operations = [
        migrations.AddField(
            model_name="rapportcsrd",
            name="bloque",
            field=models.BooleanField(
                default=False, verbose_name="rapport bloqué après publication"
            ),
        ),
    ]
