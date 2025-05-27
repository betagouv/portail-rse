"""
Ce script permet de supprimer automatiquement tout compte qui s'y serait fait inviter pour tester le service.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from entreprises.models import Entreprise
from habilitations.models import Habilitation
from users.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        if entreprise := Entreprise.objects.filter(siren="000000001").first():
            Habilitation.objects.filter(entreprise=entreprise).exclude(
                user__email=settings.SUPPORT_EMAIL
            ).delete()

            # dans le cas où un testeur supprime l'utilisateur contact de l'entreprise, le réajouter
            if not Habilitation.objects.filter(
                entreprise=entreprise, user__email=settings.SUPPORT_EMAIL
            ):
                contact = User.objects.get(email=settings.SUPPORT_EMAIL)
                Habilitation.ajouter(entreprise, contact, fonctions="Démo")
