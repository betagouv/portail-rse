from dataclasses import dataclass
from enum import Enum

from django.db import models

from utils.models import TimestampedModel


class Categorie(Enum):
    GENERAL = {"id": "informations-generales", "label": "Informations générales"}
    ENVIRONNEMENT = {"id": "environnement", "label": "Environnement"}
    SOCIAL = {"id": "social", "label": "Social"}
    GOUVERNANCE = {"id": "gouvernance", "label": "Gouvernance"}


@dataclass
class ExigenceDePublication:
    code: str
    nom: str
    categorie: "Categorie"


EXIGENCES_DE_PUBLICATION = {
    "B1": ExigenceDePublication("B1", "Base d’établissement", Categorie.GENERAL),
    "B2": ExigenceDePublication(
        "B2",
        "Pratiques, politiques et initiatives futures pour une transition vers une économie plus durable",
        Categorie.GENERAL,
    ),
    "B3": ExigenceDePublication(
        "B3", "Énergie et émissions de gaz à effet de serre", Categorie.ENVIRONNEMENT
    ),
    "B4": ExigenceDePublication(
        "B4", "Pollution de l’air, de l’eau et des sols", Categorie.ENVIRONNEMENT
    ),
    "B5": ExigenceDePublication("B5", "Biodiversité", Categorie.ENVIRONNEMENT),
    "B6": ExigenceDePublication("B6", "Eau", Categorie.ENVIRONNEMENT),
    "B7": ExigenceDePublication(
        "B7",
        "Utilisation des ressources, économie circulaire et gestion des déchets",
        Categorie.ENVIRONNEMENT,
    ),
    "B8": ExigenceDePublication(
        "B8", "Effectifs : caractéristiques générales", Categorie.SOCIAL
    ),
    "B9": ExigenceDePublication(
        "B9", "Effectifs : santé et sécurité", Categorie.SOCIAL
    ),
    "B10": ExigenceDePublication(
        "B10",
        "Effectifs : rémunération, négociation collective et formation",
        Categorie.SOCIAL,
    ),
    "B11": ExigenceDePublication(
        "B11",
        "Condamnations et amendes en matière de lutte contre la corruption et les actes de corruption",
        Categorie.GOUVERNANCE,
    ),
    "C1": ExigenceDePublication(
        "C1",
        "Stratégie : modèle économique et initiatives liées à la durabilité",
        Categorie.GENERAL,
    ),
    "C2": ExigenceDePublication(
        "C2",
        "Description des pratiques, des politiques et des initiatives futures pour une transition vers une économie plus durable ",
        Categorie.GENERAL,
    ),
    "C3": ExigenceDePublication(
        "C3",
        "Cibles de réduction des émissions de GES et transition climatique",
        Categorie.ENVIRONNEMENT,
    ),
    "C4": ExigenceDePublication("C4", "Risques climatiques", Categorie.ENVIRONNEMENT),
    "C5": ExigenceDePublication(
        "C5",
        "Caractéristiques supplémentaires (générales) des effectifs",
        Categorie.SOCIAL,
    ),
    "C6": ExigenceDePublication(
        "C6",
        "Informations complémentaires sur les effectifs de l'entreprise – Politiques et procédures en matière de droits de l’homme ",
        Categorie.SOCIAL,
    ),
    "C7": ExigenceDePublication(
        "C7", "Incidents graves en matière de droits de l’homme", Categorie.SOCIAL
    ),
    "C8": ExigenceDePublication(
        "C8",
        "Recettes de certains secteurs et exclusion des indices de référence de l'UE",
        Categorie.GOUVERNANCE,
    ),
    "C9": ExigenceDePublication(
        "C9",
        "Ratio femmes/hommes au sein de l'organe de gouvernance",
        Categorie.GOUVERNANCE,
    ),
}


class RapportVSME(TimestampedModel):
    entreprise = models.ForeignKey(
        "entreprises.Entreprise",
        on_delete=models.CASCADE,
        related_name="rapports_vsme",
    )
    annee = models.PositiveIntegerField(
        verbose_name="année du rapport VSME",
    )

    class Meta:
        verbose_name = "rapport VSME"
        verbose_name_plural = "rapports VSME"
        constraints = [
            models.UniqueConstraint(
                fields=["entreprise", "annee"],
                name="unique_rapport_annuel",
            ),
        ]
        indexes = [models.Index(fields=["annee"])]


class Indicateur(TimestampedModel):
    rapport_vsme = models.ForeignKey(
        "RapportVSME",
        on_delete=models.CASCADE,  # models.SET_NULL si un indicateur peut se trouver dans plusieurs réglementations à terme ?
        # blank=True,
        # null=True,
        # Si d'autres réglementations peuvent avoir des indicateurs
        related_name="indicateurs",
    )
    schema_id = models.CharField(
        max_length=42, verbose_name="id du schéma descriptif de l'indicateur"
    )  # type B1-24-a-i-P1
    schema_version = models.PositiveIntegerField(
        verbose_name="numéro de version du schéma descriptif de l'indicateur", default=1
    )
    data = models.JSONField(
        null=True, blank=True, verbose_name="donnée brute saisie par l'utilisateur"
    )
    # est_complete ?

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["rapport_vsme", "schema_id"],
                name="unique_indicateur_par_rapport",
            ),
        ]
        indexes = [models.Index(fields=["schema_id"])]
