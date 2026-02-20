import copy
import json
import os
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.urls.base import reverse
from django.utils.functional import cached_property

from utils.combustibles import COMBUSTIBLES
from utils.models import TimestampedModel
from vsme.forms import NON_PERTINENT_FIELD_NAME


ANNEE_DEBUT_VSME = 2020  # Première année où les rapports VSME peuvent être créés


def get_annee_dernier_exercice_clos(entreprise):
    """
    Retourne l'année du dernier exercice clos pour une entreprise.
    Si l'entreprise n'a pas de date de clôture définie, retourne N-1.
    """
    annee_en_cours = date.today().year
    if not entreprise or not entreprise.date_cloture_exercice:
        return annee_en_cours - 1
    # Si la date de clôture de cette année est déjà passée, l'exercice de cette année est clos
    date_cloture = entreprise.date_cloture_exercice + relativedelta(year=annee_en_cours)
    if date_cloture < date.today():
        return annee_en_cours
    return annee_en_cours - 1


def get_annee_rapport_par_defaut(entreprise=None):
    return get_annee_dernier_exercice_clos(entreprise)


def get_annee_max_valide(entreprise=None):
    return get_annee_dernier_exercice_clos(entreprise) + 1


def get_annees_valides(entreprise=None):
    annee_max = get_annee_max_valide(entreprise)
    return list(range(ANNEE_DEBUT_VSME, annee_max + 1))


def annee_est_valide(annee, entreprise=None):
    return ANNEE_DEBUT_VSME <= annee <= get_annee_max_valide(entreprise)


def validate_annee_rapport(value):
    """
    Validateur pour le champ annee du modèle RapportVSME.
    Valide sans contexte d'entreprise (utilise l'année calendaire).
    La validation complète avec l'entreprise est faite dans les vues.
    """
    # Validation de base : entre 2020 et N+1 calendaire
    annee_max = date.today().year + 1
    if not (ANNEE_DEBUT_VSME <= value <= annee_max):
        raise ValidationError(
            f"L'année du rapport doit être entre {ANNEE_DEBUT_VSME} et {annee_max}"
        )


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
        return [
            exigence
            for code, exigence in EXIGENCES_DE_PUBLICATION.items()
            if exigence.categorie == self
        ]


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

    def indicateurs(self):
        return self.load_json_schema().keys()


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
        remplissable=True,
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
        remplissable=True,
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
        remplissable=True,
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
        "https://portail-rse.beta.gouv.fr/vsme/c1-strategie-modele-dentreprise-et-durabilite-initiatives-connexes/",
        remplissable=True,
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
        "https://portail-rse.beta.gouv.fr/vsme/c4-risques-climatiques/",
        remplissable=True,
    ),
    "C5": ExigenceDePublication(
        "C5",
        "Caractéristiques supplémentaires (générales) des effectifs",
        Categorie.SOCIAL,
        "https://portail-rse.beta.gouv.fr/vsme/c5-caracteristiques-suppl%C3%A9mentaires-du-personnel/",
        remplissable=True,
    ),
    "C6": ExigenceDePublication(
        "C6",
        "Informations complémentaires sur les effectifs de l'entreprise – Politiques et procédures en matière de droits de l’homme ",
        Categorie.SOCIAL,
        "https://portail-rse.beta.gouv.fr/vsme/c6-politiques-et-procedures-en-mati%C3%A8re-de-droits-de-lhomme/",
        remplissable=True,
    ),
    "C7": ExigenceDePublication(
        "C7",
        "Incidents graves en matière de droits de l’homme",
        Categorie.SOCIAL,
        "https://portail-rse.beta.gouv.fr/vsme/c7-incidents-graves-en-mati%C3%A8re-de-droits-de-lhomme/",
        remplissable=True,
    ),
    "C8": ExigenceDePublication(
        "C8",
        "Recettes de certains secteurs et exclusion des indices de référence de l'UE",
        Categorie.GOUVERNANCE,
        "https://portail-rse.beta.gouv.fr/vsme/c8-chiffre-daffaires-de-certains-secteurs-et-exclusion-des-indices-de-reference-de-lunion/",
        remplissable=True,
    ),
    "C9": ExigenceDePublication(
        "C9",
        "Ratio de mixité au sein de l'organe de gouvernance",
        Categorie.GOUVERNANCE,
        "https://portail-rse.beta.gouv.fr/vsme/c9-ratio-de-mixite-au-sein-des-organes-de-gouvernance/",
        remplissable=True,
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
        validators=[validate_annee_rapport],
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

    def indicateurs_applicables_par_exigence(self, exigence_de_publication):
        exigence_de_publication_schema = exigence_de_publication.load_json_schema()
        indicateurs_applicables = [
            ind
            for ind in exigence_de_publication_schema
            if self.indicateur_est_applicable(ind)[0]
        ]
        return indicateurs_applicables

    @cached_property
    def indicateurs_applicables(self):
        indicateurs_applicables = []
        for exigence_de_publication in self.exigences_de_publication_applicables():
            if exigence_de_publication.remplissable:
                for indicateur_schema_id in exigence_de_publication.indicateurs():
                    if self.indicateur_est_applicable(indicateur_schema_id)[0]:
                        indicateurs_applicables.append(indicateur_schema_id)
        return indicateurs_applicables

    def indicateur_est_applicable(self, indicateur_schema_id) -> tuple[bool, str]:
        if indicateur_schema_id.startswith("C"):  # indicateurs module complet
            if self.choix_module != "complet":
                B1_url = reverse(
                    "vsme:exigence_de_publication_vsme", args=[self.id, "B1"]
                )
                explication_non_applicable = f"l'entreprise a sélectionné uniquement le module de base dans <a class='fr-link' href='{B1_url}' target='_blank' rel='noopener external'>l'indicateur 'Base d'établissement' de B1</a>"
                return (False, explication_non_applicable)
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
                explication_non_applicable = (
                    "l'entreprise n'a pas sélectionné une base consolidée dans l'indicateur 'Type de périmètre'"
                    if not base_consolidee
                    else ""
                )
                return (base_consolidee, explication_non_applicable)
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
                B1_url = reverse(
                    "vsme:exigence_de_publication_vsme", args=[self.id, "B1"]
                )
                explication_non_applicable = (
                    f"la forme juridique renseignée par l'entreprise dans <a class='fr-link' href='{B1_url}' target='_blank' rel='noopener external'>l'indicateur 'Forme juridique' de B1</a> n'est pas une coopérative"
                    if not est_cooperative
                    else ""
                )
                return (est_cooperative, explication_non_applicable)
            case ["B8", "39", "c"]:  # indicateur effectifs par pays
                plusieurs_pays_d_exercice = len(self.pays) > 1
                B1_url = reverse(
                    "vsme:exigence_de_publication_vsme", args=[self.id, "B1"]
                )
                explication_non_applicable = (
                    f"l'entreprise n'a pas renseigné plusieurs pays d'exercice dans <a class='fr-link' href='{B1_url}' target='_blank' rel='noopener external'>l'indicateur 'Pays d'exercice' de B1</a>"
                    if not plusieurs_pays_d_exercice
                    else ""
                )
                return (plusieurs_pays_d_exercice, explication_non_applicable)
            case ["C5", _]:  # indicateurs supplémentaires des effectifs
                nombre_salaries = self.nombre_salaries
                if nombre_salaries is not None and nombre_salaries < 50:
                    B1_url = reverse(
                        "vsme:exigence_de_publication_vsme", args=[self.id, "B1"]
                    )
                    explication_non_applicable = f"le nombre de salariés renseigné dans <a class='fr-link' href='{B1_url}' target='_blank' rel='noopener external'>l'indicateur 'Nombre de salariés' de B1</a> est inférieur à 50"
                    return (False, explication_non_applicable)
                else:
                    return (True, "")
            case ["C4", "58"]:  # indicateur impacts financiers des risques climatiques
                risques_climatiques = self.risques_climatiques
                if not risques_climatiques:
                    explication_non_applicable = f"l'entreprise n'a pas renseigné de risque climatique dans l'indicateur 'Aléas et risques climatiques recensés'"
                    return (False, explication_non_applicable)
                else:
                    return (True, "")
            case _:
                return (True, "")

    def indicateurs_completes_par_exigence(self, exigence_de_publication):
        return self.indicateurs.filter(
            schema_id__startswith=exigence_de_publication.code
        ).values_list("schema_id", flat=True)

    @cached_property
    def indicateurs_completes(self):
        return self.indicateurs.values_list("schema_id", flat=True)

    def progression_par_exigence(self, exigence_de_publication):
        if not exigence_de_publication.remplissable:
            return {"total": 0, "complet": 0, "pourcent": 0}

        indicateurs_exigences = set(exigence_de_publication.indicateurs())
        indicateurs_applicables = indicateurs_exigences.intersection(
            set(self.indicateurs_applicables)
        )
        indicateurs_completes = indicateurs_exigences.intersection(
            set(self.indicateurs_completes)
        )
        indicateurs_completes_et_applicables = indicateurs_applicables.intersection(
            indicateurs_completes
        )
        complet = len(indicateurs_completes_et_applicables)
        total = len(indicateurs_applicables)
        if total:
            pourcent = (complet / total) * 100
        else:
            pourcent = 100
        return {"total": total, "complet": complet, "pourcent": int(pourcent)}

    def progression_par_categorie(self, categorie):
        complet, total, pourcent = 0, 0, 0
        for exigence_de_publication in self.exigences_de_publication_applicables():
            if exigence_de_publication.categorie == categorie:
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
        for exigence_de_publication in self.exigences_de_publication_applicables():
            progression_exigence = self.progression_par_exigence(
                exigence_de_publication
            )
            complet += progression_exigence["complet"]
            total += progression_exigence["total"]
        if total:
            pourcent = (complet / total) * 100
        return {"total": total, "complet": complet, "pourcent": int(pourcent)}

    def exigences_de_publication_applicables(self):
        choix_module = self.choix_module
        exigences_de_publication_module_complet = EXIGENCES_DE_PUBLICATION.values()
        exigences_de_publication_module_base = [
            exigence
            for exigence in exigences_de_publication_module_complet
            if exigence.code.startswith("B")
        ]
        match choix_module:
            case "base":
                return exigences_de_publication_module_base
            case "complet":
                return exigences_de_publication_module_complet

    def get_choix_module(self):
        module_par_defaut = "complet"
        indicateur_choix_module = "B1-24-a"
        try:
            choix_module = self.indicateurs.get(
                schema_id=indicateur_choix_module
            ).data.get("choix_module", module_par_defaut)
        except ObjectDoesNotExist:
            choix_module = module_par_defaut
        return choix_module

    choix_module = cached_property(get_choix_module)

    def get_pays(self):
        indicateur_pays = "B1-24-e-vi"
        try:
            codes_pays = self.indicateurs.get(schema_id=indicateur_pays).data.get(
                "pays", []
            )
        except ObjectDoesNotExist:
            codes_pays = []
        return codes_pays

    pays = cached_property(get_pays)

    def get_nombre_salaries(self) -> int | None:
        indicateur_nombre_salaries = "B1-24-e-v"
        try:
            nombre_salaries = self.indicateurs.get(
                schema_id=indicateur_nombre_salaries
            ).data.get("nombre_salaries")
        except ObjectDoesNotExist:
            nombre_salaries = None
        return nombre_salaries

    nombre_salaries = cached_property(get_nombre_salaries)

    def get_risques_climatiques(self) -> list:
        indicateur_schema_id = "C4-57"
        try:
            indicateur_risques_climatiques = self.indicateurs.get(
                schema_id=indicateur_schema_id
            )
            if indicateur_risques_climatiques.est_non_pertinent:
                return []
            risques_climatiques = indicateur_risques_climatiques.data.get(
                "aleas_et_risques_climatiques", []
            )
            risques_climatiques = [
                {
                    "id": risque["id_risque"],
                    "description": risque["description"],
                }
                for risque in risques_climatiques
            ]
        except ObjectDoesNotExist:
            risques_climatiques = []
        return risques_climatiques

    risques_climatiques = cached_property(get_risques_climatiques)


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
    _data = models.JSONField(
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

    @property
    def schema(self):
        schema_exigence = ExigenceDePublication.par_indicateur_schema_id(
            self.schema_id
        ).load_json_schema()
        return schema_exigence[self.schema_id]

    @property
    def data(self) -> dict:
        data = copy.deepcopy(self._data) if self._data else {}
        # décode les champs de type nombre_decimal qui sont encodés en string lors du stockage
        for champ in self.schema["champs"]:
            match champ["type"]:
                case "nombre_decimal":
                    string_data = data.get(champ["id"])
                    if string_data:
                        # retype la donnée uniquement si elle est présente
                        data[champ["id"]] = Decimal(string_data)
                case "tableau":
                    for colonne in champ["colonnes"]:
                        if colonne["type"] == "nombre_decimal":
                            for ligne in data.get(champ["id"], []):
                                string_data = ligne.get(colonne["id"])
                                if string_data:
                                    ligne[colonne["id"]] = Decimal(string_data)
                case "tableau_lignes_fixes":
                    for colonne in champ["colonnes"]:
                        if colonne["type"] == "nombre_decimal":
                            for ligne in data.get(champ["id"], {}):
                                string_data = data[champ["id"]][ligne].get(
                                    colonne["id"]
                                )
                                if string_data:
                                    data[champ["id"]][ligne][colonne["id"]] = Decimal(
                                        string_data
                                    )

        # ajoute les données calculées non stockées
        data = ajoute_donnes_calculees(self.schema_id, self.rapport_vsme, data)

        return data

    @data.setter
    def data(self, cleaned_data):
        self._data = cleaned_data

    @property
    def est_non_pertinent(self) -> bool:
        return bool(self._data and self._data.get(NON_PERTINENT_FIELD_NAME))


def ajoute_donnes_calculees(indicateur_schema_id, rapport_vsme, data):
    match indicateur_schema_id:
        case "B3-29-p1":
            consommation_electricite = data.get("consommation_electricite_par_type")
            if consommation_electricite:
                consommation_renouvelable = (
                    consommation_electricite.get("consommation_energie", {}).get(
                        "renouvelable"
                    )
                    or 0
                )
                consommation_non_renouvelable = (
                    consommation_electricite.get("consommation_energie", {}).get(
                        "non_renouvelable"
                    )
                    or 0
                )
                total = consommation_renouvelable + consommation_non_renouvelable
                data["consommation_electricite_par_type"] = {
                    "consommation_energie": {
                        "renouvelable": consommation_renouvelable,
                        "non_renouvelable": consommation_non_renouvelable,
                        "total": total,
                    }
                }
        case "B3-29-p2":
            consommation_renouvelable = 0
            consommation_non_renouvelable = 0
            combustibles = data.get("consommation_energie_par_combustible")
            if combustibles:
                for index, combustible in enumerate(combustibles):
                    type_combustible = combustible.get("type_combustible")
                    infos_combustible = COMBUSTIBLES.get(type_combustible)
                    if infos_combustible:
                        if infos_combustible["etat_chimique"] == "solide":
                            infos_combustible["densite"] = "n/a"
                        data["consommation_energie_par_combustible"][index].update(
                            {k: v for k, v in infos_combustible.items()}
                        )
                        quantite = data["consommation_energie_par_combustible"][
                            index
                        ].get("quantite")
                        if quantite:
                            match infos_combustible["unite"]:
                                case "t":
                                    masse_en_t = quantite
                                case "L" | "m3":
                                    masse_en_t = (
                                        quantite * infos_combustible["densite"] / 1000
                                    )
                            nvc_en_mwh_par_t = infos_combustible["NCV"] * Decimal(
                                "0.277778"
                            )
                            # NCV est en TJ/Gg dans infos_combustible
                            # 1 TJ = 277.778 MWh et 1 Gg = 1000 t
                            energie = arrondit_2_decimales_si_superieur_a_1(
                                masse_en_t * nvc_en_mwh_par_t
                            )
                            data["consommation_energie_par_combustible"][index][
                                "energie"
                            ] = energie
                            match infos_combustible["etat_renouvelabilite"]:
                                case "renouvelable":
                                    consommation_renouvelable += energie
                                case "non_renouvelable":
                                    consommation_non_renouvelable += energie
            autres_combustibles = data.get("consommation_energie_autres_combustibles")
            if autres_combustibles:
                for combustible in autres_combustibles:
                    if combustible.get("energie"):
                        match combustible.get("etat_renouvelabilite"):
                            case "renouvelable":
                                consommation_renouvelable += combustible["energie"]
                            case "non_renouvelable":
                                consommation_non_renouvelable += combustible["energie"]
            data["consommation_combustible_par_type"] = {
                "consommation_energie": {
                    "renouvelable": arrondit_2_decimales_si_superieur_a_1(
                        consommation_renouvelable
                    ),
                    "non_renouvelable": arrondit_2_decimales_si_superieur_a_1(
                        consommation_non_renouvelable
                    ),
                    "total": arrondit_2_decimales_si_superieur_a_1(
                        consommation_renouvelable + consommation_non_renouvelable
                    ),
                }
            }
        case "B3-30":
            emissions = data.get("estimation_emissions_GES", {}).get(
                "emissions_brutes_GES"
            )
            if emissions:
                emissions_scope_1 = emissions.get("scope_1") or 0
                emissions_scope_2 = emissions.get("scope_2_localisation") or 0
                total = emissions_scope_1 + emissions_scope_2
                data["estimation_emissions_GES"]["emissions_brutes_GES"][
                    "total"
                ] = total

                indicateur_chiffre_affaires = "B1-24-e-iv"
                try:
                    chiffre_affaires = rapport_vsme.indicateurs.get(
                        schema_id=indicateur_chiffre_affaires
                    ).data.get("chiffre_affaires")
                    if chiffre_affaires:
                        intensite_GES = arrondit_2_decimales_si_superieur_a_1(
                            total / chiffre_affaires
                        )
                    else:
                        intensite_GES = "n/a"
                except ObjectDoesNotExist:
                    intensite_GES = "n/a"
                data["intensite_GES"] = intensite_GES
        case "B10-42-b":
            remuneration_hommes = data.get("remuneration_horaire_hommes")
            remuneration_femmes = data.get("remuneration_horaire_femmes")
            if remuneration_hommes and remuneration_femmes is not None:
                ecart_remuneration_hommes_femmes = round(
                    100
                    * (remuneration_hommes - remuneration_femmes)
                    / remuneration_hommes,
                    2,
                )
                data["ecart_remuneration_hommes_femmes"] = (
                    ecart_remuneration_hommes_femmes
                )
        case "B10-42-c":
            nombre_salaries_conventions_collectives = data.get(
                "nombre_salaries_conventions_collectives"
            )
            if nombre_salaries_conventions_collectives is not None:
                nombre_salaries = rapport_vsme.nombre_salaries
                if nombre_salaries:
                    taux = (
                        100 * nombre_salaries_conventions_collectives / nombre_salaries
                    )
                    if taux < 20:
                        tranche_taux = "0-20"
                    elif taux < 40:
                        tranche_taux = "20-40"
                    elif taux < 60:
                        tranche_taux = "40-60"
                    elif taux < 80:
                        tranche_taux = "60-80"
                    else:
                        tranche_taux = "80-100"
                    data["taux_couverture_conventions_collectives"] = tranche_taux
                else:
                    data["taux_couverture_conventions_collectives"] = "n/a"
        case "B10-42-d":
            if total_heure_formation_par_genre := data.get(
                "nombre_heures_formation_par_genre"
            ):
                try:
                    indicateur_nombre_salaries_par_genre = "B8-39-b"
                    nombre_salaries_par_genre = rapport_vsme.indicateurs.get(
                        schema_id=indicateur_nombre_salaries_par_genre
                    ).data.get("effectifs_genre")
                    if nombre_salaries_par_genre:
                        for genre in nombre_salaries_par_genre:
                            total_heure_formation = (
                                data["nombre_heures_formation_par_genre"]
                                .get(genre, {})
                                .get("total_heures_formation")
                            )
                            if total_heure_formation is not None:
                                nombre_salaries = nombre_salaries_par_genre[genre].get(
                                    "nombre_salaries"
                                )
                                if nombre_salaries:
                                    nombre_moyen_heures_formation = round(
                                        total_heure_formation / nombre_salaries, 2
                                    )
                                else:
                                    nombre_moyen_heures_formation = "n/a"
                                data["nombre_heures_formation_par_genre"][genre][
                                    "nombre_moyen_heures_formation"
                                ] = nombre_moyen_heures_formation
                except ObjectDoesNotExist:
                    pass
        case "C5-59":
            nombre_femmes = data.get("nombre_femmes_parmi_encadrement")
            nombre_hommes = data.get("nombre_hommes_parmi_encadrement")
            if nombre_hommes and nombre_femmes is not None:
                ratio = round(nombre_femmes / nombre_hommes, 2)
                data["ratio_femmes_hommes_encadrement"] = ratio
            elif nombre_hommes == 0:
                data["ratio_femmes_hommes_encadrement"] = "n/a"
        case "C8-63":
            chiffre_affaires_charbon = data.get("chiffre_affaires_charbon") or 0
            chiffre_affaires_petrole = data.get("chiffre_affaires_petrole") or 0
            chiffre_affaires_gaz = data.get("chiffre_affaires_gaz") or 0
            data["chiffre_affaires_combustibles_fossiles"] = (
                chiffre_affaires_charbon
                + chiffre_affaires_petrole
                + chiffre_affaires_gaz
            )
    return data


def arrondit_2_decimales_si_superieur_a_1(valeur):
    return round(valeur, 2) if valeur > 1 else valeur
