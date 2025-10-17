import json
import os
from dataclasses import dataclass
from enum import Enum

from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from utils.models import TimestampedModel


class Categorie(Enum):
    GENERAL = {"id": "informations-generales", "label": "Informations générales"}
    ENVIRONNEMENT = {"id": "environnement", "label": "Environnement"}
    SOCIAL = {"id": "social", "label": "Social"}
    GOUVERNANCE = {"id": "gouvernance", "label": "Gouvernance"}

    @classmethod
    def par_id(cls, categorie_id):
        for c in cls:
            if c.value["id"] == categorie_id:
                return c

    def exigences_de_publication(self):
        return (
            exigence
            for code, exigence in EXIGENCES_DE_PUBLICATION.items()
            if exigence.categorie == self
        )


@dataclass
class ExigenceDePublication:
    code: str
    nom: str
    categorie: "Categorie"
    url_infos: str = ""
    remplissable: bool = (
        False  # nous intégrons les exigences de publication une par une, toutes ne le sont pas encore
    )

    def load_json_schema(self):
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = f"schemas/{self.code}.json"
        full_path = os.path.join(current_dir, file_path)
        with open(full_path, "r") as file:
            return json.load(file)

    @classmethod
    def par_code(cls, exigence_de_publication_code):
        return EXIGENCES_DE_PUBLICATION[exigence_de_publication_code]

    @classmethod
    def par_indicateur_schema_id(cls, indicateur_schema_id):
        code = indicateur_schema_id.split("-")[0]
        return cls.par_code(code)


EXIGENCES_DE_PUBLICATION = {
    "B1": ExigenceDePublication(
        "B1",
        "Base d’établissement",
        Categorie.GENERAL,
        "https://portail-rse.beta.gouv.fr/vsme/b1-base-de-preparation/",
        remplissable=True,
    ),
    "B2": ExigenceDePublication(
        "B2",
        "Pratiques, politiques et initiatives futures pour une transition vers une économie plus durable",
        Categorie.GENERAL,
        "https://portail-rse.beta.gouv.fr/vsme/b2-pratiques-politiques-et-initiatives-futures-en-vue-de-la-transition-vers-une-economie-plus-durable/",
        remplissable=True,
    ),
    "B3": ExigenceDePublication(
        "B3",
        "Énergie et émissions de gaz à effet de serre",
        Categorie.ENVIRONNEMENT,
        "https://portail-rse.beta.gouv.fr/vsme/b3-energie-et-emissions-de-gaz-a-effet-de-serre/",
    ),
    "B4": ExigenceDePublication(
        "B4",
        "Pollution de l’air, de l’eau et des sols",
        Categorie.ENVIRONNEMENT,
        "https://portail-rse.beta.gouv.fr/vsme/b4-pollution-de-l-air-de-l-eau-et-des-sols/",
        remplissable=True,
    ),
    "B5": ExigenceDePublication(
        "B5",
        "Biodiversité",
        Categorie.ENVIRONNEMENT,
        "https://portail-rse.beta.gouv.fr/vsme/b5-biodiversite/",
    ),
    "B6": ExigenceDePublication(
        "B6",
        "Eau",
        Categorie.ENVIRONNEMENT,
        "https://portail-rse.beta.gouv.fr/vsme/b6-eau/",
        remplissable=True,
    ),
    "B7": ExigenceDePublication(
        "B7",
        "Utilisation des ressources, économie circulaire et gestion des déchets",
        Categorie.ENVIRONNEMENT,
        "https://portail-rse.beta.gouv.fr/vsme/b7-utilisation-des-ressources-economie-circulaire-et-gestion-des-dechets/",
        remplissable=True,
    ),
    "B8": ExigenceDePublication(
        "B8",
        "Effectifs : caractéristiques générales",
        Categorie.SOCIAL,
        "https://portail-rse.beta.gouv.fr/vsme/b8-effectifs-caracteristiques-generales/",
        remplissable=True,
    ),
    "B9": ExigenceDePublication(
        "B9",
        "Effectifs : santé et sécurité",
        Categorie.SOCIAL,
        "https://portail-rse.beta.gouv.fr/vsme/b9-effectifs-sante-et-securite/",
        remplissable=True,
    ),
    "B10": ExigenceDePublication(
        "B10",
        "Effectifs : rémunération, négociation collective et formation",
        Categorie.SOCIAL,
        "https://portail-rse.beta.gouv.fr/vsme/b10-personnel-remuneration-negociation-collective-et-formation/",
    ),
    "B11": ExigenceDePublication(
        "B11",
        "Condamnations et amendes en matière de lutte contre la corruption et les actes de corruption",
        Categorie.GOUVERNANCE,
        "https://portail-rse.beta.gouv.fr/vsme/b11-condamnations-et-amendes-pour-corruption-et-versement-de-pots-de-vin/",
        remplissable=True,
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
    "C4": ExigenceDePublication(
        "C4",
        "Risques climatiques",
        Categorie.ENVIRONNEMENT,
    ),
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

    def indicateurs_actifs(self, exigence_de_publication):
        exigence_de_publication_schema = exigence_de_publication.load_json_schema()
        indicateurs_actifs = [
            ind
            for ind in exigence_de_publication_schema
            if self.indicateur_est_actif(ind)
        ]
        return indicateurs_actifs

    def indicateur_est_actif(self, indicateur_schema_id):
        match indicateur_schema_id.split("-"):
            case ["B1", "24", "d"]:  # indicateur liste filiales
                indicateur_type_de_perimetre = "B1-24-c"
                try:
                    base_consolidee = (
                        self.indicateurs.get(
                            schema_id=indicateur_type_de_perimetre
                        ).data.get("type_perimetre")
                        == "consolidee"
                    )
                except ObjectDoesNotExist:
                    base_consolidee = False
                return base_consolidee
            case ["B2", "26", p]:  # indicateurs spécifiques aux coopératives
                indicateur_forme_juridique = "B1-24-e-i"
                try:
                    forme_juridique = self.indicateurs.get(
                        schema_id=indicateur_forme_juridique
                    ).data
                    est_cooperative = forme_juridique.get(
                        "coopérative"
                    ) or forme_juridique.get("forme_juridique") in ("51", "63")
                except ObjectDoesNotExist:
                    est_cooperative = False
                return est_cooperative
            case _:
                return True

    def indicateurs_completes(self, exigence_de_publication):
        return self.indicateurs.filter(
            schema_id__startswith=exigence_de_publication.code
        ).values_list("schema_id", flat=True)

    def progression_par_exigence(self, exigence_de_publication):
        if not exigence_de_publication.remplissable:
            return {"total": 0, "complet": 0, "pourcent": 0}
        indicateurs_actifs = set(self.indicateurs_actifs(exigence_de_publication))
        indicateurs_completes = set(self.indicateurs_completes(exigence_de_publication))
        indicateurs_completes_et_actifs = indicateurs_actifs.intersection(
            indicateurs_completes
        )
        complet = len(indicateurs_completes_et_actifs)
        total = len(indicateurs_actifs)
        pourcent = (complet / total) * 100
        return {"total": total, "complet": complet, "pourcent": int(pourcent)}

    def progression_par_categorie(self, categorie):
        complet, total, pourcent = 0, 0, 0
        for exigence_de_publication in categorie.exigences_de_publication():
            progression_exigence = self.progression_par_exigence(
                exigence_de_publication
            )
            complet += progression_exigence["complet"]
            total += progression_exigence["total"]
        if total:
            pourcent = (complet / total) * 100
        return {"total": total, "complet": complet, "pourcent": int(pourcent)}

    def progression(self):
        complet, total, pourcent = 0, 0, 0
        for exigence_de_publication in EXIGENCES_DE_PUBLICATION.values():
            progression_exigence = self.progression_par_exigence(
                exigence_de_publication
            )
            complet += progression_exigence["complet"]
            total += progression_exigence["total"]
        if total:
            pourcent = (complet / total) * 100
        return {"total": total, "complet": complet, "pourcent": int(pourcent)}

    def pays(self):
        indicateur_pays = "B1-24-e-vi"
        try:
            codes_pays = self.indicateurs.get(schema_id=indicateur_pays).data.get(
                "pays"
            )
        except ObjectDoesNotExist:
            codes_pays = []
        return codes_pays


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
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
        verbose_name="donnée brute saisie par l'utilisateur",
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
