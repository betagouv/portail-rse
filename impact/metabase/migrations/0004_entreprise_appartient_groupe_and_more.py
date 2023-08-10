# Generated by Django 4.2 on 2023-08-02 13:14
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("metabase", "0003_entreprise_date_cloture_exercice_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="entreprise",
            name="appartient_groupe",
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name="entreprise",
            name="comptes_consolides",
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name="entreprise",
            name="tranche_bilan_consolide",
            field=models.CharField(max_length=9, null=True),
        ),
        migrations.AddField(
            model_name="entreprise",
            name="tranche_chiffre_affaires_consolide",
            field=models.CharField(max_length=9, null=True),
        ),
    ]