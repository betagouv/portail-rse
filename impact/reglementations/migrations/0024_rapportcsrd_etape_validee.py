# Generated by Django 4.2.16 on 2024-10-18 14:56
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("reglementations", "0023_rapportcsrd_enjeu_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="rapportcsrd",
            name="etape_validee",
            field=models.PositiveIntegerField(
                null=True, verbose_name="étape validée du rapport CSRD"
            ),
        ),
    ]
