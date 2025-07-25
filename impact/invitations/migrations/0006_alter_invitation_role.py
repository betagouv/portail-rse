# Generated by Django 5.1.11 on 2025-07-04 15:58
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("invitations", "0005_alter_invitation_inviteur"),
    ]

    operations = [
        migrations.AlterField(
            model_name="invitation",
            name="role",
            field=models.CharField(
                choices=[
                    ("proprietaire", "Propriétaire"),
                    ("editeur", "Éditeur"),
                    ("lecteur", "Lecteur"),
                ],
                max_length=20,
                verbose_name="Role (droits)",
            ),
        ),
    ]
