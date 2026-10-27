import os
import uuid

from django.db import migrations
from django.db import models


def uuid7_depuis_date(date):
    # uuid.uuid7() n'accepte pas de date : 48 bits de timestamp en ms puis 80 bits aléatoires,
    # les bits de version et de variante sont positionnés par uuid.UUID
    timestamp_ms = int(date.timestamp() * 1000)
    aleatoire = int.from_bytes(os.urandom(10))
    return uuid.UUID(int=(timestamp_ms << 80) | aleatoire, version=7)


def genere_id_public(apps, schema_editor):
    Entreprise = apps.get_model("entreprises", "Entreprise")
    entreprises = list(Entreprise.objects.only("pk", "created_at"))
    for entreprise in entreprises:
        entreprise.id_public = uuid7_depuis_date(entreprise.created_at)
    Entreprise.objects.bulk_update(entreprises, ["id_public"], batch_size=1000)


class Migration(migrations.Migration):

    dependencies = [
        (
            "entreprises",
            "0056_remove_caracteristiquesannuelles_systeme_management_energie",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="entreprise",
            name="id_public",
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.RunPython(genere_id_public, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="entreprise",
            name="id_public",
            field=models.UUIDField(default=uuid.uuid7, unique=True, editable=False),
        ),
    ]
