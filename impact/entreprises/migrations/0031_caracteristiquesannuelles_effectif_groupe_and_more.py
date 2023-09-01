# Generated by Django 4.2.3 on 2023-08-25 15:14
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("entreprises", "0030_alter_caracteristiquesannuelles_effectif"),
    ]

    operations = [
        migrations.AddField(
            model_name="caracteristiquesannuelles",
            name="effectif_groupe",
            field=models.CharField(
                blank=True,
                choices=[
                    ("0-49", "moins de 50 salariés"),
                    ("50-249", "entre 50 et 249 salariés"),
                    ("250-499", "entre 250 et 499 salariés"),
                    ("500-4999", "entre 500 et 4 999 salariés"),
                    ("5000-9999", "entre 5 000 et 9 999 salariés"),
                    ("10000+", "10 000 salariés ou plus"),
                ],
                help_text="Nombre de salariés du groupe",
                max_length=9,
                null=True,
                verbose_name="Effectif du groupe",
            ),
        ),
        migrations.AddField(
            model_name="entreprise",
            name="societe_mere_en_france",
            field=models.BooleanField(
                null=True, verbose_name="La société mère a son siège social en France"
            ),
        ),
    ]