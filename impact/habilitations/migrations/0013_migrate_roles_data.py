from django.db import migrations

ROLES_RENOMMES = (
    ("editeur", "contributeur"),
    ("proprietaire", "administrateur"),
)


def renomme_roles(apps, roles_renommes):
    Habilitation = apps.get_model("habilitations", "Habilitation")
    Invitation = apps.get_model("invitations", "Invitation")
    for ancienne_valeur, nouvelle_valeur in roles_renommes:
        Habilitation.objects.filter(role=ancienne_valeur).update(role=nouvelle_valeur)
        Invitation.objects.filter(role=ancienne_valeur).update(role=nouvelle_valeur)


def forwards(apps, schema_editor):
    renomme_roles(apps, ROLES_RENOMMES)


def backwards(apps, schema_editor):
    renomme_roles(
        apps,
        [
            (nouvelle_valeur, ancienne_valeur)
            for ancienne_valeur, nouvelle_valeur in ROLES_RENOMMES
        ],
    )


class Migration(migrations.Migration):
    dependencies = [
        ("habilitations", "0012_alter_habilitation_role"),
        ("invitations", "0009_alter_invitation_role"),
    ]

    operations = [
        migrations.RunPython(forwards, reverse_code=backwards),
    ]
