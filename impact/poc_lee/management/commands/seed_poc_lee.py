import os
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction

from entreprises.models import ActualisationCaracteristiquesAnnuelles
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from habilitations.models import Habilitation

DATE_CLOTURE = date(2025, 12, 31)
EMAIL = "demo-lee@portail-rse.test"

ENTREPRISES = [
    {
        "identifiant": "095680393",
        "denomination": "KEOLIS PAYS BASQUE",
        "code_NAF": "49.31Z",
        "code_postal": "64100",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_securite_sociale": CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
    },
    {
        "identifiant": "045850617",
        "denomination": "PRODUITS & COULEURS DU DOUAISIS",
        "code_NAF": "46.73B",
        "code_postal": "59500",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "effectif_securite_sociale": CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_MOINS_DE_10,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
    },
]


class Command(BaseCommand):
    help = "Crée les entreprises et l'utilisateur de la démo du connecteur LEE"

    def handle(self, *args, **options):
        mot_de_passe = os.getenv("POC_LEE_DEMO_PASSWORD")
        if not mot_de_passe:
            raise CommandError("POC_LEE_DEMO_PASSWORD est absent de l'environnement")
        with transaction.atomic():
            utilisateur = self.utilisateur(mot_de_passe)
            for donnees in ENTREPRISES:
                entreprise = self.entreprise(donnees)
                if not Habilitation.existe(entreprise, utilisateur):
                    Habilitation.ajouter(
                        entreprise, utilisateur, fonctions="Dirigeant·e"
                    )
        self.stdout.write(self.style.SUCCESS(f"Démo prête pour {EMAIL}"))

    def utilisateur(self, mot_de_passe):
        utilisateur, _ = get_user_model().objects.get_or_create(
            email=EMAIL,
            defaults={
                "prenom": "Démo",
                "nom": "LEE",
                "reception_actualites": False,
                "is_email_confirmed": True,
            },
        )
        utilisateur.set_password(mot_de_passe)
        utilisateur.save()
        return utilisateur

    def entreprise(self, donnees):
        entreprise, _ = Entreprise.objects.get_or_create(
            identifiant=donnees["identifiant"],
            defaults={
                "denomination": donnees["denomination"],
                "code_NAF": donnees["code_NAF"],
                "code_postal": donnees["code_postal"],
                "categorie_juridique_sirene": 5710,
                "date_cloture_exercice": DATE_CLOTURE,
                "date_derniere_qualification": date.today(),
                "est_cotee": False,
                "est_interet_public": False,
                "appartient_groupe": False,
                "est_societe_mere": False,
                "societe_mere_en_france": False,
                "comptes_consolides": False,
            },
        )
        if not entreprise.caracteristiques_annuelles(DATE_CLOTURE.year):
            entreprise.actualise_caracteristiques(
                ActualisationCaracteristiquesAnnuelles(
                    DATE_CLOTURE,
                    donnees["effectif"],
                    donnees["effectif_securite_sociale"],
                    CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
                    None,
                    None,
                    donnees["tranche_chiffre_affaires"],
                    donnees["tranche_bilan"],
                    None,
                    None,
                    False,
                    CaracteristiquesAnnuelles.CONSOMMATION_ENERGIE_MOINS_DE_2_75GWH,
                )
            ).save()
        return entreprise
