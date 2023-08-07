from django.conf import settings

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationAction
from reglementations.views.base import ReglementationStatus


class BGESReglementation(Reglementation):
    title = "BGES et plan de transition"
    description = "Le Bilan GES réglementaire a vocation à contribuer à la mise en œuvre de la stratégie de réduction des émissions de GES des entreprises. Un plan de transition est obligatoirement joint à ce bilan. Il vise à réduire les émissions de gaz à effet de serre et présente les objectifs, moyens et actions envisagées à cette fin ainsi que, le cas échéant, les actions mises en œuvre lors du précédent bilan. Ils sont mis à jour tous les quatre ans."
    more_info_url = "https://bilans-ges.ademe.fr/"

    def est_soumis(self, caracteristiques):
        return (
            caracteristiques.effectif == CaracteristiquesAnnuelles.EFFECTIF_500_ET_PLUS
            or caracteristiques.effectif_outre_mer
            == CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_250_ET_PLUS
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
            primary_action = ReglementationAction(
                "https://bilans-ges.ademe.fr/bilans/comment-publier",
                "Publier mon Bilan GES",
                external=True,
            )
        else:
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation"
            primary_action = ReglementationAction(
                "https://bilans-ges.ademe.fr/bilans",
                "Consulter les Bilans GES sur Bilans GES",
                external=True,
            )
        return ReglementationStatus(
            status, status_detail, primary_action=primary_action
        )
