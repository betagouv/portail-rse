from datetime import date

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from utils.models import TimestampedModel

DENOMINATION_MAX_LENGTH = 250


class Entreprise(TimestampedModel):
    siren = models.CharField(max_length=9, unique=True)
    denomination = models.CharField(max_length=DENOMINATION_MAX_LENGTH)
    date_cloture_exercice = models.DateField(
        verbose_name="Date de clôture du dernier exercice comptable",
        null=True,
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="habilitations.Habilitation"
    )

    def __str__(self):
        return f"{self.siren} {self.denomination}"

    @property
    def dernieres_caracteristiques_qualifiantes(self):
        for caracteristiques in CaracteristiquesAnnuelles.objects.filter(
            entreprise=self,
        ).order_by("-annee"):
            if caracteristiques.sont_qualifiantes:
                return caracteristiques

    @property
    def dernieres_caracteristiques(self):
        if caracteristiques := CaracteristiquesAnnuelles.objects.filter(
            entreprise=self,
        ).order_by("-annee"):
            return caracteristiques.first()

    def caracteristiques_annuelles(self, annee):
        try:
            return CaracteristiquesAnnuelles.objects.get(
                entreprise=self,
                annee=annee,
            )
        except ObjectDoesNotExist:
            return None

    def caracteristiques_actuelles(self):
        cette_annee = date.today().year
        if not self.date_cloture_exercice:
            # ce cas existe lorsque l'entreprise n'a pas encore été qualifiée
            return self.caracteristiques_annuelles(cette_annee - 1)
        annee_dernier_exercice_clos = (
            cette_annee
            if self.date_cloture_exercice.replace(year=cette_annee) < date.today()
            else cette_annee - 1
        )
        return self.caracteristiques_annuelles(annee_dernier_exercice_clos)

    def actualise_caracteristiques(
        self,
        date_cloture_exercice,
        effectif,
        tranche_chiffre_affaires,
        tranche_bilan,
        bdese_accord,
        systeme_management_energie,
        effectif_outre_mer=None
    ):
        caracteristiques = self.caracteristiques_annuelles(
            date_cloture_exercice.year
        ) or CaracteristiquesAnnuelles(
            entreprise=self, annee=date_cloture_exercice.year
        )
        caracteristiques.date_cloture_exercice = date_cloture_exercice
        caracteristiques.effectif = effectif
        caracteristiques.effectif_outre_mer = effectif_outre_mer
        caracteristiques.bdese_accord = bdese_accord
        caracteristiques.tranche_chiffre_affaires = tranche_chiffre_affaires
        caracteristiques.tranche_bilan = tranche_bilan
        caracteristiques.systeme_management_energie = systeme_management_energie
        return caracteristiques


class CaracteristiquesAnnuelles(TimestampedModel):
    EFFECTIF_MOINS_DE_50 = "0-49"
    EFFECTIF_ENTRE_50_ET_249 = "50-249"
    EFFECTIF_ENTRE_250_ET_299 = "250-299"
    EFFECTIF_ENTRE_300_ET_499 = "300-499"
    EFFECTIF_500_ET_PLUS = "500+"
    EFFECTIF_CHOICES = [
        (EFFECTIF_MOINS_DE_50, "moins de 50 salariés"),
        (EFFECTIF_ENTRE_50_ET_249, "entre 50 et 249 salariés"),
        (EFFECTIF_ENTRE_250_ET_299, "entre 250 et 299 salariés"),
        (EFFECTIF_ENTRE_300_ET_499, "entre 300 et 499 salariés"),
        (EFFECTIF_500_ET_PLUS, "500 salariés ou plus"),
    ]

    EFFECTIF_OUTRE_MER_MOINS_DE_250 = "0-249"
    EFFECTIF_OUTRE_MER_250_ET_PLUS = "250+"
    EFFECTIF_OUTRE_MER_CHOICES = [
        (EFFECTIF_OUTRE_MER_MOINS_DE_250, "moins de 250 salariés"),
        (EFFECTIF_OUTRE_MER_250_ET_PLUS, "250 salariés ou plus"),
    ]

    CA_MOINS_DE_700K = "0-700k"
    CA_ENTRE_700K_ET_12M = "700k-12M"
    CA_ENTRE_12M_ET_40M = "12M-40M"
    CA_ENTRE_40M_ET_50M = "40M-50M"
    CA_ENTRE_50M_ET_100M = "50M-100M"
    CA_100M_ET_PLUS = "100M+"

    CA_CHOICES = [
        (CA_MOINS_DE_700K, "moins de 700k€"),
        (CA_ENTRE_700K_ET_12M, "entre 700k€ et 12M€"),
        (CA_ENTRE_12M_ET_40M, "entre 12M€ et 40M€"),
        (CA_ENTRE_40M_ET_50M, "entre 40M€ et 50M€"),
        (CA_ENTRE_50M_ET_100M, "entre 50M€ et 100M€"),
        (CA_100M_ET_PLUS, "100M€ ou plus"),
    ]

    BILAN_MOINS_DE_350K = "0-350k"
    BILAN_ENTRE_350K_ET_6M = "350k-6M"
    BILAN_ENTRE_6M_ET_20M = "6M-20M"
    BILAN_ENTRE_20M_ET_43M = "20M-43M"
    BILAN_ENTRE_43M_ET_100M = "43M-100M"
    BILAN_100M_ET_PLUS = "100M+"

    BILAN_CHOICES = [
        (BILAN_MOINS_DE_350K, "moins de 350k€"),
        (BILAN_ENTRE_350K_ET_6M, "entre 350k€ et 6M€"),
        (BILAN_ENTRE_6M_ET_20M, "entre 6M€ et 20M€"),
        (BILAN_ENTRE_20M_ET_43M, "entre 20M€ et 43M€"),
        (BILAN_ENTRE_43M_ET_100M, "entre 43M€ et 100M€"),
        (BILAN_100M_ET_PLUS, "100M€ ou plus"),
    ]

    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    annee = models.IntegerField()
    date_cloture_exercice = models.DateField(
        verbose_name="Date de clôture de l'exercice comptable",
        null=True,
    )
    effectif = models.CharField(
        max_length=9,
        choices=EFFECTIF_CHOICES,
        verbose_name="Effectif total",
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
    tranche_chiffre_affaires = models.CharField(
        verbose_name="Chiffre d'affaires",
        max_length=9,
        choices=CA_CHOICES,
        null=True,
    )
    tranche_bilan = models.CharField(
        verbose_name="Bilan",
        max_length=9,
        choices=BILAN_CHOICES,
        null=True,
    )
    bdese_accord = models.BooleanField(
        verbose_name="L'entreprise a un accord collectif d'entreprise concernant la Base de Données Économiques, Sociales et Environnementales (BDESE)",
        default=False,  # null=True serait préférable
    )
    systeme_management_energie = models.BooleanField(
        verbose_name="L'entreprise a mis en place un système de management de l’énergie",
        null=True,
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

    @property
    def sont_qualifiantes(self):
        return bool(
            self.date_cloture_exercice
            and self.effectif
            and self.effectif_outre_mer
            and self.tranche_chiffre_affaires
            and self.tranche_bilan
            and self.bdese_accord is not None
            and self.systeme_management_energie is not None
        )
