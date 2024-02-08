from dataclasses import dataclass
from datetime import date
from enum import Enum
from enum import unique

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from utils.models import TimestampedModel

DENOMINATION_MAX_LENGTH = 250


@dataclass
class ActualisationCaracteristiquesAnnuelles:
    date_cloture_exercice: date
    effectif: str
    effectif_permanent: str
    effectif_outre_mer: str
    effectif_groupe: str
    effectif_groupe_france: str
    effectif_groupe_permanent: str
    tranche_chiffre_affaires: str
    tranche_bilan: str
    tranche_chiffre_affaires_consolide: str
    tranche_bilan_consolide: str
    bdese_accord: bool
    systeme_management_energie: bool


@unique
class CategorieJuridique(Enum):
    AUTRE = 0
    SOCIETE_ANONYME = 1
    SOCIETE_COMMANDITE_PAR_ACTIONS = 2
    SOCIETE_PAR_ACTIONS_SIMPLIFIEES = 3
    SOCIETE_EUROPEENNE = 4
    SOCIETE_COOPERATIVE_DE_PRODUCTION = 5
    SOCIETE_COOPERATIVE_AGRICOLE = 6
    SOCIETE_ASSURANCE_MUTUELLE = 7
    MUTUELLE = 8
    INSTITUTION_PREVOYANCE = 9

    @property
    def label(self):
        if self.value == self.SOCIETE_ANONYME.value:
            return "Société Anonyme"
        elif self.value == self.SOCIETE_COMMANDITE_PAR_ACTIONS.value:
            return "Société en Commandite par Actions"
        elif self.value == self.SOCIETE_COOPERATIVE_DE_PRODUCTION.value:
            return "Société Coopérative de Production"
        elif self.value == self.SOCIETE_PAR_ACTIONS_SIMPLIFIEES.value:
            return "Société par Actions Simplifiées"
        elif self.value == self.SOCIETE_EUROPEENNE.value:
            return "Société Européenne"
        elif self.value == self.SOCIETE_COOPERATIVE_AGRICOLE.value:
            return "Société Coopérative Agricole"
        elif self.value == self.SOCIETE_ASSURANCE_MUTUELLE.value:
            return "Société d'assurance à forme mutuelle"
        elif self.value == self.MUTUELLE.value:
            return "Mutuelle"
        elif self.value == self.INSTITUTION_PREVOYANCE.value:
            return "Institution de Prévoyance"
        return ""

    @staticmethod
    def est_une_SA_cooperative(categorie_juridique_sirene):
        if not categorie_juridique_sirene:
            return
        return (
            5551 <= categorie_juridique_sirene <= 5560
            or 5651 <= categorie_juridique_sirene <= 5660
            or categorie_juridique_sirene in (5543, 5547, 5643, 5647)
        )


def convertit_categorie_juridique(categorie_juridique_sirene):
    if not categorie_juridique_sirene:
        return
    elif 5308 <= categorie_juridique_sirene <= 5385:
        return CategorieJuridique.SOCIETE_COMMANDITE_PAR_ACTIONS
    elif (
        5443 <= categorie_juridique_sirene <= 5460
        or 5551 <= categorie_juridique_sirene <= 5560
        or 5651 <= categorie_juridique_sirene <= 5660
        or categorie_juridique_sirene in (5543, 5547, 5643, 5647)
    ):
        return CategorieJuridique.SOCIETE_COOPERATIVE_DE_PRODUCTION
    elif (
        5505 <= categorie_juridique_sirene <= 5515
        or 5522 <= categorie_juridique_sirene <= 5542
        or 5599 <= categorie_juridique_sirene <= 5642
        or 5670 <= categorie_juridique_sirene <= 5699
        or categorie_juridique_sirene in (5546, 5646, 5648)
    ):
        return CategorieJuridique.SOCIETE_ANONYME
    elif 5710 <= categorie_juridique_sirene <= 5785:
        return CategorieJuridique.SOCIETE_PAR_ACTIONS_SIMPLIFIEES
    elif categorie_juridique_sirene == 5800:
        return CategorieJuridique.SOCIETE_EUROPEENNE
    elif categorie_juridique_sirene in (6317, 6318):
        return CategorieJuridique.SOCIETE_COOPERATIVE_AGRICOLE
    elif categorie_juridique_sirene == 6411:
        return CategorieJuridique.SOCIETE_ASSURANCE_MUTUELLE
    elif categorie_juridique_sirene == 8210:
        return CategorieJuridique.MUTUELLE
    elif categorie_juridique_sirene == 8510:
        return CategorieJuridique.INSTITUTION_PREVOYANCE
    else:
        return CategorieJuridique.AUTRE


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
    est_cotee = models.BooleanField(
        verbose_name="L'entreprise est cotée sur un marché réglementé européen",
        null=True,
    )
    appartient_groupe = models.BooleanField(
        verbose_name="L'entreprise fait partie d'un groupe",
        null=True,
    )
    est_societe_mere = models.BooleanField(
        verbose_name="L'entreprise est la société mère du groupe",
        null=True,
    )
    societe_mere_en_france = models.BooleanField(
        verbose_name="La société mère du groupe a son siège social en France",
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

    @property
    def categorie_juridique(self):
        return convertit_categorie_juridique(self.categorie_juridique_sirene)

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
        ) or CaracteristiquesAnnuelles(annee=actualisation.date_cloture_exercice.year)
        caracteristiques.entreprise = self
        caracteristiques.date_cloture_exercice = actualisation.date_cloture_exercice
        caracteristiques.effectif = actualisation.effectif
        caracteristiques.effectif_permanent = actualisation.effectif_permanent
        caracteristiques.effectif_outre_mer = actualisation.effectif_outre_mer
        caracteristiques.effectif_groupe = actualisation.effectif_groupe
        caracteristiques.effectif_groupe_france = actualisation.effectif_groupe_france
        caracteristiques.effectif_groupe_permanent = (
            actualisation.effectif_groupe_permanent
        )
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
        (EFFECTIF_MOINS_DE_50, "entre 0 et 49 salariés"),
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
        (EFFECTIF_OUTRE_MER_MOINS_DE_250, "entre 0 et 249 salariés"),
        (EFFECTIF_OUTRE_MER_250_ET_PLUS, "250 salariés ou plus"),
    ]

    EFFECTIF_ENTRE_250_ET_499 = "250-499"
    EFFECTIF_GROUPE_CHOICES = [
        (EFFECTIF_MOINS_DE_50, "entre 0 et 49 salariés"),
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
        (CA_MOINS_DE_700K, "entre 0 et 700k€"),
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
        (BILAN_MOINS_DE_350K, "entre 0 et 350k€"),
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
        help_text="Nombre de salariés (notamment CDI, CDD et salariés à temps partiel) de l'entreprise au prorata de leur temps de présence au cours des douze mois précédents (cf. <a href='https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006072050/LEGISCTA000006177833/#LEGISCTA000006177833' target='_blank' rel='noopener'>articles L.1111-2 et L.1111-3 du Code du Travail</a>)",
        null=True,
    )
    effectif_permanent = models.CharField(
        max_length=9,
        choices=[BLANK_CHOICE] + EFFECTIF_CHOICES,
        verbose_name="Effectif permanent",
        help_text="Nombre moyen de salariés à temps plein, titulaires d'un contrat à durée indéterminée employés par l'entreprise au cours de l'exercice comptable",
        null=True,
    )
    effectif_outre_mer = models.CharField(
        max_length=9,
        choices=[BLANK_CHOICE] + EFFECTIF_OUTRE_MER_CHOICES,
        verbose_name="Effectif outre-mer",
        help_text="Nombre de salariés de l'entreprise dans les régions et départements d'outre-mer au prorata de leur temps de présence au cours des douze mois précédents",
        null=True,
    )
    effectif_groupe = models.CharField(
        # TODO: renommer en effectif_groupe_international ?
        max_length=9,
        choices=[BLANK_CHOICE] + EFFECTIF_GROUPE_CHOICES,
        verbose_name="Effectif du groupe international",
        help_text="Nombre de salariés employés par les entreprises du groupe en incluant les filiales directes ou indirectes étrangères",
        null=True,
        blank=True,
    )
    effectif_groupe_france = models.CharField(
        max_length=9,
        choices=[BLANK_CHOICE] + EFFECTIF_GROUPE_CHOICES,
        verbose_name="Effectif du groupe France",
        help_text="Nombre de salariés (notamment CDI, CDD et salariés à temps partiel) employés par les entreprises françaises du groupe au prorata de leur temps de présence au cours des douze mois précédents (cf. <a href='https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006072050/LEGISCTA000006177833/#LEGISCTA000006177833' target='_blank' rel='noopener'>articles L.1111-2 et L.1111-3 du Code du Travail</a>)",
        null=True,
        blank=True,
    )
    effectif_groupe_permanent = models.CharField(
        max_length=9,
        choices=[BLANK_CHOICE] + EFFECTIF_GROUPE_CHOICES,
        verbose_name="Effectif permanent du groupe",
        help_text="Nombre moyen de salariés à temps plein, titulaires d'un contrat à durée indéterminée employés par le groupe au cours de l'exercice comptable en incluant les filiales directes ou indirectes étrangères",
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
                and self.effectif_groupe_france
                and self.effectif_groupe_permanent
                and self.entreprise.est_societe_mere is not None
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
            and self.effectif_permanent
            and self.tranche_chiffre_affaires
            and self.tranche_bilan
            and self.entreprise.est_cotee is not None
            and self.bdese_accord is not None
            and self.systeme_management_energie is not None
            and self.groupe_est_qualifie
        )
