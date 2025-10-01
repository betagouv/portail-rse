from typing import Annotated
from typing import Literal
from typing import TypedDict
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import ValidationError

from vsme.models import ExigenceDePublication


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
    schema_id: str = Field(frozen=True, init=False)
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
