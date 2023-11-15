from django.conf import settings
from django.urls import reverse_lazy

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationStatus


CRITERE_EFFECTIF_PERMANENT = "votre effectif permanent est supérieur à 500 salariés"
CRITERE_EFFECTIF_GROUPE_PERMANENT = (
    "l'effectif permanent du groupe est supérieur à 500 salariés"
)


class DPEFReglementation(Reglementation):
    title = "Déclaration de Performance Extra-Financière"
    description = """La Déclaration de Performance Extra-Financière (dite "DPEF") est un document par l'intermédiaire duquel une entreprise détaille les implications sociales, environnementales et sociétales de sa performance et de ses activités, ainsi que son mode de gouvernance."""
    more_info_url = reverse_lazy("reglementations:fiche_dpef")

    @classmethod
    def calculate_status(
        cls,
        caracteristiques: CaracteristiquesAnnuelles,
        user: settings.AUTH_USER_MODEL,
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(caracteristiques, user):
            return reglementation_status

    @staticmethod
    def criteres_remplis(caracteristiques):
        criteres = []
        if caracteristiques.effectif_permanent in (
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        ):
            criteres.append(CRITERE_EFFECTIF_PERMANENT)
        elif (
            caracteristiques.entreprise.comptes_consolides
            and caracteristiques.effectif_groupe_permanent
            in (
                CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
            )
        ):
            criteres.append(CRITERE_EFFECTIF_GROUPE_PERMANENT)
        if (
            caracteristiques.tranche_bilan
            == CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS
        ):
            criteres.append("votre bilan est supérieur à 100M€")
        elif (
            caracteristiques.tranche_bilan_consolide
            == CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS
        ):
            criteres.append("votre bilan consolidé est supérieur à 100M€")
        elif (
            caracteristiques.entreprise.est_cotee
            and caracteristiques.tranche_bilan
            in (
                CaracteristiquesAnnuelles.BILAN_ENTRE_20M_ET_43M,
                CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
            )
        ):
            criteres.append("votre bilan est supérieur à 20M€")
        if (
            caracteristiques.tranche_chiffre_affaires
            == CaracteristiquesAnnuelles.CA_100M_ET_PLUS
        ):
            criteres.append("votre chiffre d'affaires est supérieur à 100M€")
        elif (
            caracteristiques.tranche_chiffre_affaires_consolide
            == CaracteristiquesAnnuelles.CA_100M_ET_PLUS
        ):
            criteres.append("votre chiffre d'affaires consolidé est supérieur à 100M€")

        return criteres

    @classmethod
    def est_soumis(cls, caracteristiques):
        criteres = cls.criteres_remplis(caracteristiques)
        return len(criteres) >= 2 and (
            CRITERE_EFFECTIF_PERMANENT in criteres
            or CRITERE_EFFECTIF_GROUPE_PERMANENT in criteres
        )
