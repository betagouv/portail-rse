from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from utils.models import TimestampedModel

DENOMINATION_MAX_LENGTH = 250
FONCTIONS_MAX_LENGTH = 250


class Entreprise(TimestampedModel):
    EFFECTIF_CHOICES = [
        ("petit", "moins de 50"),
        ("moyen", "entre 50 et 300"),
        ("grand", "entre 301 et 499"),
        ("sup500", "plus de 500"),
    ]

    siren = models.CharField(max_length=9, unique=True)
    denomination = models.CharField(max_length=DENOMINATION_MAX_LENGTH)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="habilitations.Habilitation"
    )
    effectif = models.CharField(
        max_length=9,
        choices=EFFECTIF_CHOICES,
        help_text="Vérifiez et confirmez le nombre de salariés",
        null=True,
    )
    bdese_accord = models.BooleanField(
        verbose_name="L'entreprise a un accord collectif d'entreprise concernant la Base de Données Économiques, Sociales et Environnementales (BDESE)",
        default=False,
    )

    def __str__(self):
        return f"{self.siren} {self.denomination}"

    @property
    def is_qualified(self):
        return self.denomination and self.effectif
