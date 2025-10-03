import json
import os
from dataclasses import dataclass
from enum import Enum
from typing import Annotated
from typing import Literal
from typing import TypedDict
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import ValidationError


class BaseChamp(BaseModel):
    id: str
    label: str
    description: str | None = None
    obligatoire: bool = False


class AutoID(BaseChamp):
    type_champ: Literal["auto_id"] = Field(alias="type")


class NombreEntier(BaseChamp):
    type_champ: Literal["nombre_entier"] = Field(alias="type")
    unité: str


class NombreDecimal(BaseChamp):
    type_champ: Literal["nombre_decimal"] = Field(alias="type")
    unité: str


class Texte(BaseChamp):
    type_champ: Literal["texte"] = Field(alias="type")
    max_length: int = 255


class Date(BaseChamp):
    type_champ: Literal["date"] = Field(alias="type")


class Geolocalisation(BaseChamp):
    type_champ: Literal["geolocalisation"] = Field(alias="type")


class ChoixBinaire(BaseChamp):
    type_champ: Literal["choix_binaire"] = Field(alias="type")


class Choix(TypedDict):
    id: str
    label: str


ChoixPredefinis = Union[
    Literal["CHOIX_PAYS"],
    Literal["CHOIX_FORME_JURIDIQUE"],
    Literal["CHOIX_NACE"],
    Literal["CHOIX_EXIGENCE_DE_PUBLICATION"],
]


class BaseChoix(BaseChamp):
    choix: list[Choix] | ChoixPredefinis


class ChoixUnique(BaseChoix):
    type_champ: Literal["choix_unique"] = Field(alias="type")


class ChoixMultiple(BaseChoix):
    type_champ: Literal["choix_multiple"] = Field(alias="type")


ChampBasique = Annotated[
    Union[
        AutoID,
        NombreEntier,
        NombreDecimal,
        Texte,
        Date,
        Geolocalisation,
        ChoixBinaire,
        ChoixUnique,
        ChoixMultiple,
    ],
    Field(discriminator="type_champ"),
]


class Tableau(BaseChamp):
    type_champ: Literal["tableau"] = Field(alias="type")
    colonnes: list[ChampBasique]


Champ = Annotated[Union[ChampBasique, Tableau], Field(discriminator="type_champ")]


class IndicateurSchemaInvalide(Exception):
    pass


class IndicateurSchema(BaseModel):
    schema_id: str = Field(frozen=True)
    titre: str
    description: str
    ancre: str
    champs: list[Champ]
    si_pertinent: bool = False

    @classmethod
    def par_schema_id(cls, schema_id):
        schema = ExigenceDePublication.par_indicateur_schema_id(
            schema_id
        ).load_json_schema()[schema_id]
        try:
            return cls.model_validate(dict(schema, schema_id=schema_id))
        except ValidationError as e:
            raise IndicateurSchemaInvalide(e)


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
    remplissable: bool = False

    def load_json_schema(self):
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

    def indicateurs_schemas(self):
        json_schema = self.load_json_schema()
        try:
            return [
                IndicateurSchema.model_validate(dict(schema, schema_id=schema_id))
                for schema_id, schema in json_schema.items()
            ]
        except ValidationError as e:
            raise IndicateurSchemaInvalide(e)


EXIGENCES_DE_PUBLICATION = {
    "B1": ExigenceDePublication(
        "B1",
        "Base d'établissement",
        Categorie.GENERAL,
        "https://portail-rse.beta.gouv.fr/vsme/b1-base-de-preparation/",
        remplissable=True,
    ),
    "B2": ExigenceDePublication(
        "B2",
        "Pratiques, politiques et initiatives futures pour une transition vers une économie plus durable",
        Categorie.GENERAL,
        "https://portail-rse.beta.gouv.fr/vsme/b2-pratiques-politiques-et-initiatives-futures-en-vue-de-la-transition-vers-une-economie-plus-durable/",
    ),
    "B3": ExigenceDePublication(
        "B3",
        "Énergie et émissions de gaz à effet de serre",
        Categorie.ENVIRONNEMENT,
        "https://portail-rse.beta.gouv.fr/vsme/b3-energie-et-emissions-de-gaz-a-effet-de-serre/",
    ),
    "B4": ExigenceDePublication(
        "B4",
        "Pollution de l'air, de l'eau et des sols",
        Categorie.ENVIRONNEMENT,
        "https://portail-rse.beta.gouv.fr/vsme/b4-pollution-de-l-air-de-l-eau-et-des-sols/",
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
    ),
    "B7": ExigenceDePublication(
        "B7",
        "Utilisation des ressources, économie circulaire et gestion des déchets",
        Categorie.ENVIRONNEMENT,
        "https://portail-rse.beta.gouv.fr/vsme/b7-utilisation-des-ressources-economie-circulaire-et-gestion-des-dechets/",
    ),
    "B8": ExigenceDePublication(
        "B8",
        "Effectifs : caractéristiques générales",
        Categorie.SOCIAL,
        "https://portail-rse.beta.gouv.fr/vsme/b8-effectifs-caracteristiques-generales/",
    ),
    "B9": ExigenceDePublication(
        "B9",
        "Effectifs : santé et sécurité",
        Categorie.SOCIAL,
        "https://portail-rse.beta.gouv.fr/vsme/b9-effectifs-sante-et-securite/",
    ),
    "B10": ExigenceDePublication(
        "B10",
        "Effectifs : rémunération, négociation collective et formation",
        Categorie.SOCIAL,
        "https://portail-rse.beta.gouv.fr/vsme/b10-personnel-remuneration-negociation-collective-et-formation/",
    ),
    "B11": ExigenceDePublication(
        "B11",
        "Condamnations et amendes en matière de lutte contre la corruption et les actes de corruption",
        Categorie.GOUVERNANCE,
        "https://portail-rse.beta.gouv.fr/vsme/b11-condamnations-et-amendes-pour-corruption-et-versement-de-pots-de-vin/",
    ),
    "C1": ExigenceDePublication(
        "C1",
        "Stratégie : modèle économique et initiatives liées à la durabilité",
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
        "Informations complémentaires sur les effectifs de l'entreprise – Politiques et procédures en matière de droits de l'homme ",
        Categorie.SOCIAL,
    ),
    "C7": ExigenceDePublication(
        "C7", "Incidents graves en matière de droits de l'homme", Categorie.SOCIAL
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
