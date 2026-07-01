"""
Ce script permet de :
- supprimer automatiquement tout compte utilisateur de l'entreprise test qui s'y serait fait inviter pour tester le service après la durée de test paramétrée
- supprimer toute entreprise du compte utilisateur test autre que l'entreprise test
- forcer le profil utilisateur test en simple membre d'entreprise (non conseiller RSE) dans le cas où il a été modifié
"""

from datetime import date
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

from entreprises.models import Entreprise
from habilitations.models import Habilitation
from users.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        if entreprise_test := Entreprise.objects.filter(
            siren=settings.SIREN_ENTREPRISE_TEST
        ).first():
            date_min_habilitation = date.today() - timedelta(
                days=settings.MAX_JOURS_HABILITATION
            )
            Habilitation.objects.filter(
                entreprise=entreprise_test, created_at__lt=date_min_habilitation
            ).exclude(user__email=settings.SUPPORT_EMAIL).exclude(
                user__email=settings.USER_TEST_EMAIL
            ).delete()

            # dans le cas où un testeur supprime l'utilisateur support ou l'utilisateur test de l'entreprise test, le réajouter
            for email in set([settings.SUPPORT_EMAIL, settings.USER_TEST_EMAIL]):
                try:
                    utilisateur = User.objects.get(email=email)
                except User.DoesNotExist:
                    continue
                if not Habilitation.existe(entreprise_test, utilisateur):
                    Habilitation.ajouter(entreprise_test, utilisateur, fonctions="Démo")
                # dans le cas où le profil de l'utilisateur test a été modifié en conseiller RSE, supprimer le statut conseiller RSE
                if (
                    utilisateur.email == settings.USER_TEST_EMAIL
                    and utilisateur.is_conseiller_rse
                ):
                    utilisateur.is_conseiller_rse = False
                    utilisateur.save()

            # dans le cas où une autre entreprise a été ajoutée sur l'utilisateur test, la supprimer
            Habilitation.objects.filter(user__email=settings.USER_TEST_EMAIL).exclude(
                entreprise=entreprise_test
            ).delete()
