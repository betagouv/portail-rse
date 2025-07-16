from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationStatus


class DispositifAntiCorruption(Reglementation):
    id = "dispositif-anti-corruption"
    title = "Dispositif anti-corruption"
    more_info_url = "https://portail-rse.beta.gouv.fr/fiches-reglementaires/dispositif-anti-corruption/"
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
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(caracteristiques):
            return reglementation_status

        if cls.est_soumis(caracteristiques):
            status = ReglementationStatus.STATUS_SOUMIS
            status_detail = f"Vous êtes soumis à cette réglementation car {' et '.join(cls.criteres_remplis(caracteristiques))}."
        else:
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation."
        return ReglementationStatus(status, status_detail)
