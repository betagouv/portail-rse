from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "entreprises",
            "0055_caracteristiquesannuelles_tranche_consommation_energie_finale",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="caracteristiquesannuelles",
            name="systeme_management_energie",
        ),
    ]
