import uuid

from django.db import migrations
from django.db import models


def genere_id_public(apps, schema_editor):
    Entreprise = apps.get_model("entreprises", "Entreprise")
    entreprises = list(Entreprise.objects.only("pk"))
    for entreprise in entreprises:
        entreprise.id_public = uuid.uuid4()
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
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
    ]
