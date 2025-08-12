from django.db import models
from django_jsonform.models.fields import JSONField

from utils.models import TimestampedModel

# pertinent à mettre dans l'indicateur ou à l'extérieur (dans ce cas, un élément "pertinent" + un élément "Indicateur") ?
# comment générer tous les indicateurs en bdd ?

# déclaratif
# {
#   "id": "B1.1",
#   "label": "Liste des filiales",
#   "type": "multi-entry",
#   "category": "général",
#   "section": "B1",
#   "description": "Champ permettant aux entreprises de rentrer chaque filiale avec l’adresse.",
#   "fields": [
#     {
#       "label": "Nom de la filiale",
#       "type": "text"
#     },
#     {
#       "label": "Adresse",
#       "type": "text"
#     }
#   ],
#   "required": true,
#   "dynamic": false
# }

# conditionnel déclaratif
# {
#   "if": {
#     "indicator": "B1.forme_juridique",
#     "equals": "Coopérative"
#   },
#   "then": {
#     "enable": ["B2.participation_gouvernance", "B2.investissement_ESS"]
#   }
# }

# demander sur dev-django s'ils ont des bibliothèques ou retour d'expérience
# contacter transition écologique


# les conditions connues actuellement :
#  - une exigence de publication doit être remplie (B1)
#  - un indicateur doit être rempli avec une valeur spécifique (Coopérative), sinon ne pas remplir l'exigence de publication
#  - un indicateur doit être rempli avec une valeur spécifique (Effectif): exigence de publication obligatoire sinon exigence de publication facultative

# reprendre Etape 1 étpae CSRD


class IndicateurTableau(TimestampedModel):
    type = "tableau"
    ITEMS_SCHEMA = {
        "type": "list",
        "items": {
            "type": "dict",
            "default": None,
            "keys": {
                "pertinent": {
                    "type": "boolean",
                    "title": "Pertinent selon votre situation",
                },
                "label": {"type": "string"},
                "link": {
                    "type": "string",
                    "choices": ["Eggs", "Juice", "Milk"],
                },
                "new_tab": {"type": "boolean", "title": "Open in new tab"},
            },
        },
    }

    pertinent = models.BooleanField(default=True)
    items = JSONField(schema=ITEMS_SCHEMA)


class IndicateurNombre(TimestampedModel):
    type = "nombre"
    ITEMS_SCHEMA = {
        "type": "integer",
        "default": None,
    }

    pertinent = models.BooleanField(default=True)
    valeur = JSONField(schema=ITEMS_SCHEMA)


class VSME(TimestampedModel):
    indicateur_tableau = models.ForeignKey(
        IndicateurTableau,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    indicateur_nombre = models.ForeignKey(
        IndicateurNombre,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
