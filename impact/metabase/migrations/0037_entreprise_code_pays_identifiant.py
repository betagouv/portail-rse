from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("metabase", "0036_analyseia_etat_v2_analyseia_message_v2_and_more"),
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
            field=models.CharField(max_length=20),
        ),
        migrations.AddField(
            model_name="entreprise",
            name="code_pays",
            field=models.CharField(default="FRA", max_length=3),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name="entreprise",
            constraint=models.UniqueConstraint(
                fields=("code_pays", "identifiant"),
                name="metabase_entreprise_unique_code_pays_identifiant",
            ),
        ),
    ]
