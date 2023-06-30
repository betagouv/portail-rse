from django.conf import settings

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationStatus


class AuditEnergetiqueReglementation(Reglementation):
    title = "Audit énergétique"
    description = "Le code de l'énergie prévoit la réalisation d’un audit énergétique pour les grandes entreprises de plus de 250 salariés, afin qu’elles mettent en place une stratégie d’efficacité énergétique de leurs activités. L’audit énergétique permet de repérer les gisements d’économies d’énergie chez les plus gros consommateurs professionnels (tertiaires et industriels). L’audit doit dater de moins de 4 ans."
    more_info_url = ""

    def est_soumis(self, caracteristiques):
        return (
            caracteristiques.effectif
            in (
                CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
                CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
                CaracteristiquesAnnuelles.EFFECTIF_500_ET_PLUS,
            )
        ) or (
            caracteristiques.tranche_bilan
            in (
                CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
                CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
            )
            and caracteristiques.tranche_chiffre_affaires
            in (
                CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
                CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
            )
        )

    def calculate_status(
        self,
        caracteristiques: CaracteristiquesAnnuelles,
        user: settings.AUTH_USER_MODEL,
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(caracteristiques, user):
            return reglementation_status

        if self.est_soumis(caracteristiques):
            status = ReglementationStatus.STATUS_SOUMIS
            status_detail = "Vous êtes soumis à cette réglementation"
        else:
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation"
        return ReglementationStatus(status, status_detail)
