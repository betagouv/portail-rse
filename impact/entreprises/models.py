from dataclasses import dataclass
from datetime import date
from enum import Enum

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from utils.models import TimestampedModel

DENOMINATION_MAX_LENGTH = 250


@dataclass
class ActualisationCaracteristiquesAnnuelles:
    date_cloture_exercice: date
    effectif: str
    effectif_outre_mer: str
    effectif_groupe: str
    tranche_chiffre_affaires: str
    tranche_bilan: str
    tranche_chiffre_affaires_consolide: str
    tranche_bilan_consolide: str
    bdese_accord: bool
    systeme_management_energie: bool


class CategorieJuridique(Enum):
    SOCIETE_ANONYME = 1
    SOCIETE_COMMANDITE_PAR_ACTION = 2
    SOCIETE_PAR_ACTION_SIMPLIFIEE = 3
    SOCIETE_EUROPEENNE = 4


def conversion_categorie_juridique(categorie_juridique_sirene):
    if 5308 <= categorie_juridique_sirene <= 5385:
        return CategorieJuridique.SOCIETE_COMMANDITE_PAR_ACTION
    elif 5005 <= categorie_juridique_sirene <= 5699:
        return CategorieJuridique.SOCIETE_ANONYME
    elif 5710 <= categorie_juridique_sirene <= 5785:
        return CategorieJuridique.SOCIETE_PAR_ACTION_SIMPLIFIEE
    elif categorie_juridique_sirene == 5800:
        return CategorieJuridique.SOCIETE_EUROPEENNE
    else:
        return


class Entreprise(TimestampedModel):
    siren = models.CharField(max_length=9, unique=True)
    denomination = models.CharField(max_length=DENOMINATION_MAX_LENGTH)
    date_derniere_qualification = models.DateField(
        verbose_name="Date de la dernière qualification",
        null=True,
    )
    categorie_juridique_sirene = models.IntegerField(null=True)
    date_cloture_exercice = models.DateField(
        verbose_name="Date de clôture du dernier exercice comptable",
        null=True,
    )
    appartient_groupe = models.BooleanField(
        verbose_name="L'entreprise fait partie d'un groupe",
        null=True,
    )
    societe_mere_en_france = models.BooleanField(
        verbose_name="La société mère a son siège social en France",
        null=True,
    )
    comptes_consolides = models.BooleanField(
        verbose_name="Le groupe d'entreprises établit des comptes consolidés", null=True
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
        self, actualisation: ActualisationCaracteristiquesAnnuelles
    ):
        caracteristiques = self.caracteristiques_annuelles(
            actualisation.date_cloture_exercice.year
        ) or CaracteristiquesAnnuelles(
            entreprise=self, annee=actualisation.date_cloture_exercice.year
        )
        caracteristiques.date_cloture_exercice = actualisation.date_cloture_exercice
        caracteristiques.effectif = actualisation.effectif
        caracteristiques.effectif_outre_mer = actualisation.effectif_outre_mer
        caracteristiques.effectif_groupe = actualisation.effectif_groupe
        caracteristiques.tranche_chiffre_affaires = (
            actualisation.tranche_chiffre_affaires
        )
        caracteristiques.tranche_bilan = actualisation.tranche_bilan
        caracteristiques.tranche_chiffre_affaires_consolide = (
            actualisation.tranche_chiffre_affaires_consolide
        )
        caracteristiques.tranche_bilan_consolide = actualisation.tranche_bilan_consolide
        caracteristiques.bdese_accord = actualisation.bdese_accord
        caracteristiques.systeme_management_energie = (
            actualisation.systeme_management_energie
        )
        return caracteristiques


BLANK_CHOICE = ("", "Sélectionnez une réponse")


class CaracteristiquesAnnuelles(TimestampedModel):
    EFFECTIF_MOINS_DE_50 = "0-49"
    EFFECTIF_ENTRE_50_ET_249 = "50-249"
    EFFECTIF_ENTRE_250_ET_299 = "250-299"
    EFFECTIF_ENTRE_300_ET_499 = "300-499"
    EFFECTIF_ENTRE_500_ET_4999 = "500-4999"
    EFFECTIF_ENTRE_5000_ET_9999 = "5000-9999"
    EFFECTIF_10000_ET_PLUS = "10000+"
    EFFECTIF_CHOICES = [
        (EFFECTIF_MOINS_DE_50, "moins de 50 salariés"),
        (EFFECTIF_ENTRE_50_ET_249, "entre 50 et 249 salariés"),
        (EFFECTIF_ENTRE_250_ET_299, "entre 250 et 299 salariés"),
        (EFFECTIF_ENTRE_300_ET_499, "entre 300 et 499 salariés"),
        (EFFECTIF_ENTRE_500_ET_4999, "entre 500 et 4 999 salariés"),
        (EFFECTIF_ENTRE_5000_ET_9999, "entre 5 000 et 9 999 salariés"),
        (EFFECTIF_10000_ET_PLUS, "10 000 salariés ou plus"),
    ]

    EFFECTIF_OUTRE_MER_MOINS_DE_250 = "0-249"
    EFFECTIF_OUTRE_MER_250_ET_PLUS = "250+"
    EFFECTIF_OUTRE_MER_CHOICES = [
        (EFFECTIF_OUTRE_MER_MOINS_DE_250, "moins de 250 salariés"),
        (EFFECTIF_OUTRE_MER_250_ET_PLUS, "250 salariés ou plus"),
    ]

    EFFECTIF_ENTRE_250_ET_499 = "250-499"
    EFFECTIF_GROUPE_CHOICES = [
        (EFFECTIF_MOINS_DE_50, "moins de 50 salariés"),
        (EFFECTIF_ENTRE_50_ET_249, "entre 50 et 249 salariés"),
        (EFFECTIF_ENTRE_250_ET_499, "entre 250 et 499 salariés"),
        (EFFECTIF_ENTRE_500_ET_4999, "entre 500 et 4 999 salariés"),
        (EFFECTIF_ENTRE_5000_ET_9999, "entre 5 000 et 9 999 salariés"),
        (EFFECTIF_10000_ET_PLUS, "10 000 salariés ou plus"),
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
        choices=[BLANK_CHOICE] + EFFECTIF_CHOICES,
        verbose_name="Effectif",
        help_text="Nombre de salariés de l'entreprise",
        null=True,
    )
    effectif_outre_mer = models.CharField(
        max_length=9,
        choices=[BLANK_CHOICE] + EFFECTIF_OUTRE_MER_CHOICES,
        verbose_name="Effectif outre-mer",
        help_text="Nombre de salariés dans les régions et départements d'outre-mer",
        null=True,
    )
    effectif_groupe = models.CharField(
        max_length=9,
        choices=[BLANK_CHOICE] + EFFECTIF_GROUPE_CHOICES,
        verbose_name="Effectif du groupe",
        help_text="Nombre de salariés du groupe",
        null=True,
        blank=True,
    )
    tranche_chiffre_affaires = models.CharField(
        verbose_name="Chiffre d'affaires",
        max_length=9,
        choices=[BLANK_CHOICE] + CA_CHOICES,
        null=True,
    )
    tranche_bilan = models.CharField(
        verbose_name="Bilan",
        max_length=9,
        choices=[BLANK_CHOICE] + BILAN_CHOICES,
        null=True,
    )
    tranche_chiffre_affaires_consolide = models.CharField(
        verbose_name="Chiffre d'affaires consolidé du groupe",
        max_length=9,
        choices=[BLANK_CHOICE] + CA_CHOICES,
        null=True,
        blank=True,
    )
    tranche_bilan_consolide = models.CharField(
        verbose_name="Bilan consolidé du groupe",
        max_length=9,
        choices=[BLANK_CHOICE] + BILAN_CHOICES,
        null=True,
        blank=True,
    )
    bdese_accord = models.BooleanField(
        verbose_name="L'entreprise a un accord collectif d'entreprise concernant la Base de Données Économiques, Sociales et Environnementales (BDESE)",
        null=True,
    )
    systeme_management_energie = models.BooleanField(
        verbose_name="L'entreprise a mis en place un système de management de l’énergie",
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
    def groupe_est_qualifie(self):
        if self.entreprise.appartient_groupe is None:
            return False
        elif not self.entreprise.appartient_groupe:
            return True
        else:
            comptes_consolides_sont_qualifies = bool(
                not self.entreprise.comptes_consolides
                or (
                    self.tranche_chiffre_affaires_consolide
                    and self.tranche_bilan_consolide
                )
            )
            return bool(
                self.effectif_groupe
                and self.entreprise.societe_mere_en_france is not None
                and self.entreprise.comptes_consolides is not None
                and comptes_consolides_sont_qualifies
            )

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
            and self.groupe_est_qualifie
        )
