from django.db import models

from utils.models import TimestampedModel


EXIGENCES_DE_PUBLICATION = {
    "B1": "Base d’établissement",
    "B2": "Pratiques, politiques et initiatives futures pour une transition vers une économie plus durable",
    "B3": "Énergie et émissions de gaz à effet de serre",
    "B4": "Pollution de l’air, de l’eau et des sols",
    "B5": "Biodiversité",
    "B6": "Eau",
    "B7": "Utilisation des ressources, économie circulaire et gestion des déchets",
    "B8": "Effectifs : caractéristiques générales",
    "B9": "Effectifs : santé et sécurité",
    "B10": "Effectifs : rémunération, négociation collective et formation",
    "B11": "Condamnations et amendes en matière de lutte contre la corruption et les actes de corruption",
    "C1": "Stratégie : modèle économique et initiatives liées à la durabilité",
    "C2": "Description des pratiques, des politiques et des initiatives futures pour une transition vers une économie plus durable ",
    "C3": "Cibles de réduction des émissions de GES et transition climatique",
    "C4": "Risques climatiques",
    "C5": "Caractéristiques supplémentaires (générales) des effectifs",
    "C6": "Informations complémentaires sur les effectifs de l'entreprise – Politiques et procédures en matière de droits de l’homme ",
    "C7": "Incidents graves en matière de droits de l’homme",
    "C8": "Recettes de certains secteurs et exclusion des indices de référence de l'UE",
    "C9": "Ratio femmes/hommes au sein de l'organe de gouvernance",
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
