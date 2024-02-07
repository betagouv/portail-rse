from django.conf import settings
from django.urls import reverse_lazy

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationStatus


class DispositifAntiCorruption(Reglementation):
    title = "Dispositif anti-corruption"
    description = """La loi dite « loi Sapin 2 » désigne la loi du 9 décembre 2016 relative à la transparence, à la lutte contre la corruption et à la modernisation de la vie économique.
        Elle impose à certaines entreprises la mise en place de mesures destinées à prévenir, détecter et sanctionner la commission, en France ou à l’étranger, de faits de corruption ou de trafic d’influence.
        Ces mesures sont diverses : code de bonne conduite, dispositif d’alerte interne, cartographie des risques, évaluation des clients et fournisseurs,
        procédures de contrôles comptables, formation du personnel exposé, régime disciplinaire propre à sanctionner les salariés en cas de violation du code de conduite,
        dispositif de contrôle et d’évaluation interne des mesures mises en œuvre."""
    more_info_url = reverse_lazy("reglementations:fiche_dispositif_anticorruption")
    tag = "tag-gouvernance"
    summary = "Se doter d'un dispositif efficace pour lutter contre la corruption et le trafic d'influence."

    @classmethod
    def est_suffisamment_qualifiee(cls, caracteristiques):
        return (
            caracteristiques.effectif is not None
            and caracteristiques.tranche_chiffre_affaires is not None
            and caracteristiques.entreprise.appartient_groupe is not None
            and (
                not caracteristiques.entreprise.appartient_groupe
                or (
                    caracteristiques.effectif_groupe is not None
                    and caracteristiques.entreprise.comptes_consolides is not None
                    and (
                        not caracteristiques.entreprise.comptes_consolides
                        or caracteristiques.tranche_chiffre_affaires_consolide
                        is not None
                    )
                )
            )
        )

    @classmethod
    def criteres_remplis(cls, caracteristiques):
        criteres = []
        if caracteristiques.effectif in (
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        ):
            criteres.append("votre effectif est supérieur à 500 salariés")
        elif (
            caracteristiques.effectif_groupe
            in (
                CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
            )
            and caracteristiques.entreprise.societe_mere_en_france
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
        super().est_soumis(caracteristiques)
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
