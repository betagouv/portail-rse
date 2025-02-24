from django.db import migrations


def rename_csrd_step_id(apps, schema_editor):
    old_id = "collection-donnees-entreprise"
    new_id = "selection-informations"

    RapportCSRD = apps.get_model("reglementations", "RapportCSRD")
    rapports = RapportCSRD.objects.filter(etape_validee=old_id).all()

    for rapport in rapports:
        rapport.etape_validee = new_id
        rapport.save()


class Migration(migrations.Migration):

    dependencies = [
        ("reglementations", "0028_rapportcsrd_bloque"),
    ]

    operations = [
        migrations.RunPython(
            rename_csrd_step_id,
            reverse_code=migrations.RunPython.noop,
        )
    ]
