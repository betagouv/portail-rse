from django.db import migrations
from django.db import models

from utils.pays import CODES_PAYS_ISO_3166_1


class Migration(migrations.Migration):
    dependencies = [
        ("entreprises", "0057_entreprise_id_public"),
    ]

    operations = [
        migrations.RenameField(
            model_name="entreprise",
            old_name="siren",
            new_name="identifiant",
        ),
        migrations.AlterField(
            model_name="entreprise",
            name="identifiant",
            field=models.CharField(
                max_length=20,
                verbose_name="Identifiant externe (SIREN pour la France)",
            ),
        ),
        migrations.AddField(
            model_name="entreprise",
            name="code_pays",
            field=models.CharField(
                choices=CODES_PAYS_ISO_3166_1.items(),
                default="FRA",
                max_length=3,
            ),
        ),
        migrations.AddConstraint(
            model_name="entreprise",
            constraint=models.UniqueConstraint(
                fields=("code_pays", "identifiant"),
                name="unique_code_pays_identifiant",
            ),
        ),
    ]
