from django.conf import settings
from django.urls import reverse_lazy

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationStatus


class DispositifAlerteReglementation(Reglementation):
    title = "Dispositif d’alerte"
    more_info_url = reverse_lazy("reglementations:fiche_dispositif_alerte")
    tag = "tag-gouvernance"
    summary = (
        "Avoir une procédure interne de recueil et de traitement de ces signalements."
    )

    @classmethod
    def est_suffisamment_qualifiee(cls, caracteristiques):
        return caracteristiques.effectif is not None

    @classmethod
    def criteres_remplis(cls, caracteristiques):
        criteres = []
        if caracteristiques.effectif not in (
            CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
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
