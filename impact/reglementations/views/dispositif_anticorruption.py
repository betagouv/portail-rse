from django.conf import settings

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationStatus


class DispositifAntiCorruption(Reglementation):
    title = "Dispositif anti-corruption"
    description = """La loi du 9 décembre 2016 (dite "loi Sapin 2") impose aux entreprises d'au moins 500 salariés la mise en place de mesures préventives anticorruption : cartographie des risques, procédures d’évaluation de la situation des clients, fournisseurs, information et sanctions des salariés."""
    more_info_url = ""

    @staticmethod
    def criteres_remplis(caracteristiques):
        criteres = []
        if caracteristiques.effectif in (
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        ):
            criteres.append("votre effectif est supérieur à 500 salariés")
        elif caracteristiques.effectif_groupe in (
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        ):
            criteres.append("l'effectif du groupe est supérieur à 500 salariés")

        if (
            caracteristiques.tranche_chiffre_affaires
            == CaracteristiquesAnnuelles.CA_100M_ET_PLUS
        ):
            criteres.append(
                "votre chiffre d'affaires est supérieur à 100 millions d'euros"
            )
        elif (
            caracteristiques.tranche_chiffre_affaires_consolide
            == CaracteristiquesAnnuelles.CA_100M_ET_PLUS
        ):
            criteres.append(
                "votre chiffre d'affaires consolidé est supérieur à 100 millions d'euros"
            )
        return criteres

    @classmethod
    def est_soumis(cls, caracteristiques):
        return len(cls.criteres_remplis(caracteristiques)) == 2

    @classmethod
    def calculate_status(
        cls,
        caracteristiques: CaracteristiquesAnnuelles,
        user: settings.AUTH_USER_MODEL,
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(caracteristiques, user):
            return reglementation_status

        if cls.est_soumis(caracteristiques):
            status = ReglementationStatus.STATUS_SOUMIS
            status_detail = f"Vous êtes soumis à cette réglementation car {' et '.join(cls.criteres_remplis(caracteristiques))}."
        else:
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation."
        return ReglementationStatus(status, status_detail)
