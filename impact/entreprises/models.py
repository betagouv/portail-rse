from datetime import date

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from utils.models import TimestampedModel

DENOMINATION_MAX_LENGTH = 250


class Entreprise(TimestampedModel):
    siren = models.CharField(max_length=9, unique=True)
    denomination = models.CharField(max_length=DENOMINATION_MAX_LENGTH)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="habilitations.Habilitation"
    )

    def __str__(self):
        return f"{self.siren} {self.denomination}"

    @property
    def est_qualifiee(self):
        caracteristiques_actuelles = self.caracteristiques_actuelles()
        return (
            bool(caracteristiques_actuelles)
            and caracteristiques_actuelles.effectif
            and caracteristiques_actuelles.effectif_outre_mer
        )

    def caracteristiques_annuelles(self, annee):
        try:
            return CaracteristiquesAnnuelles.objects.get(
                entreprise=self,
                annee=annee,
            )
        except ObjectDoesNotExist:
            return None

    def caracteristiques_actuelles(self):
        return self.caracteristiques_annuelles(date.today().year - 1)

    def actualise_caracteristiques(
        self, effectif, bdese_accord, effectif_outre_mer=None
    ):
        caracteristiques = (
            self.caracteristiques_actuelles()
            or CaracteristiquesAnnuelles(entreprise=self, annee=date.today().year - 1)
        )
        caracteristiques.effectif = effectif
        caracteristiques.effectif_outre_mer = effectif_outre_mer
        caracteristiques.bdese_accord = bdese_accord
        return caracteristiques


class CaracteristiquesAnnuelles(TimestampedModel):
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

    EFFECTIF_OUTRE_MER_MOINS_DE_250 = "0-249"
    EFFECTIF_OUTRE_MER_250_ET_PLUS = "250+"
    EFFECTIF_OUTRE_MER_CHOICES = [
        (EFFECTIF_OUTRE_MER_MOINS_DE_250, "moins de 250 salariés"),
        (EFFECTIF_OUTRE_MER_250_ET_PLUS, "250 salariés ou plus"),
    ]

    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    annee = models.IntegerField()
    effectif = models.CharField(
        max_length=9,
        choices=EFFECTIF_CHOICES,
        help_text="Vérifiez et confirmez le nombre de salariés",
        null=True,
    )
    effectif_outre_mer = models.CharField(
        max_length=9,
        choices=EFFECTIF_OUTRE_MER_CHOICES,
        verbose_name="Effectif outre-mer",
        help_text="Nombre de salariés dans les régions et départements d'outre-mer",
        null=True,
    )
    bdese_accord = models.BooleanField(
        verbose_name="L'entreprise a un accord collectif d'entreprise concernant la Base de Données Économiques, Sociales et Environnementales (BDESE)",
        default=False,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["entreprise", "annee"],
                name="uniques_caracteristiques_annuelles",
            )
        ]
        verbose_name = "Caractéristiques annuelles"
        verbose_name_plural = "Caractéristiques annuelles"
