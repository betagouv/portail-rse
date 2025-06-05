from django.conf import settings

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationStatus


class DispositifAlerteReglementation(Reglementation):
    title = "Dispositif d’alerte"
    more_info_url = (
        "https://portail-rse.beta.gouv.fr/fiches-reglementaires/dispositif-dalerte/"
    )
    tag = "tag-gouvernance"
    summary = (
        "Avoir une procédure interne de recueil et de traitement de ces signalements."
    )

    @classmethod
    def est_suffisamment_qualifiee(cls, caracteristiques):
        return caracteristiques.effectif_securite_sociale is not None

    @classmethod
    def criteres_remplis(cls, caracteristiques):
        criteres = []
        if caracteristiques.effectif_securite_sociale in (
            CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_ENTRE_50_ET_249,
            CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_ENTRE_250_ET_499,
            CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_500_ET_PLUS,
        ):
            criteres.append("votre effectif est supérieur à 50 salariés")
        return criteres

    @classmethod
    def est_soumis(cls, caracteristiques):
        super().est_soumis(caracteristiques)
        return bool(cls.criteres_remplis(caracteristiques))

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
            status_detail = f"Vous êtes soumis à cette réglementation car {', '.join(cls.criteres_remplis(caracteristiques))}."
        else:
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation."
        return ReglementationStatus(status, status_detail)
