from datetime import date

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from utils.models import TimestampedModel

DENOMINATION_MAX_LENGTH = 250
FONCTIONS_MAX_LENGTH = 250


class Entreprise(TimestampedModel):
    siren = models.CharField(max_length=9, unique=True)
    denomination = models.CharField(max_length=DENOMINATION_MAX_LENGTH)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="habilitations.Habilitation"
    )

    def __str__(self):
        return f"{self.siren} {self.denomination}"

    @property
    def is_qualified(self):
        return bool(self.get_current_evolution())

    def get_evolution(self, annee):
        try:
            return Evolution.objects.get(
                entreprise=self,
                annee=annee,
            )
        except ObjectDoesNotExist:
            return None

    def get_current_evolution(self):
        return self.get_evolution(date.today().year)

    def set_current_evolution(entreprise, effectif, bdese_accord):
        return Evolution.objects.create(
            entreprise=entreprise,
            annee=date.today().year,
            effectif=effectif,
            bdese_accord=bdese_accord,
        )


class Evolution(TimestampedModel):
    EFFECTIF_MOINS_DE_50 = "0-49"
    EFFECTIF_ENTRE_50_ET_299 = "50-299"
    EFFECTIF_ENTRE_300_ET_499 = "300-499"
    EFFECTIF_500_ET_PLUS = "500+"
    EFFECTIF_CHOICES = [
        (EFFECTIF_MOINS_DE_50, "moins de 50 salariés"),
        (EFFECTIF_ENTRE_50_ET_299, "entre 50 et 299 salariés"),
        (EFFECTIF_ENTRE_300_ET_499, "entre 300 et 499 salariés"),
        (EFFECTIF_500_ET_PLUS, "500 salariés ou plus"),
    ]

    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, default=None)
    annee = models.IntegerField()
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
