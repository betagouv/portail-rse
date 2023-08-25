from django.conf import settings

from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import is_user_attached_to_entreprise
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationAction
from reglementations.views.base import ReglementationStatus


class BGESReglementation(Reglementation):
    title = "BGES et plan de transition"
    description = "Le bilan GES réglementaire a vocation à contribuer à la mise en œuvre de la stratégie de réduction des émissions de GES des entreprises. Un plan de transition est obligatoirement joint à ce bilan. Il vise à réduire les émissions de gaz à effet de serre et présente les objectifs, moyens et actions envisagées à cette fin ainsi que, le cas échéant, les actions mises en œuvre lors du précédent bilan. Ils sont mis à jour tous les quatre ans."
    more_info_url = "https://bilans-ges.ademe.fr/"

    def criteres_remplis(self, caracteristiques):
        criteres = []
        if caracteristiques.effectif == CaracteristiquesAnnuelles.EFFECTIF_500_ET_PLUS:
            criteres.append("votre effectif est supérieur à 500 salariés")

        if (
            caracteristiques.effectif_outre_mer
            == CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_250_ET_PLUS
        ):
            criteres.append("votre effectif outre-mer est supérieur à 250 salariés")
        return criteres

    def est_soumis(self, caracteristiques):
        return self.criteres_remplis(caracteristiques)

    def calculate_status(
        self,
        caracteristiques: CaracteristiquesAnnuelles,
        user: settings.AUTH_USER_MODEL,
    ) -> ReglementationStatus:
        NON_SOUMIS_PRIMARY_ACTION = ReglementationAction(
            "https://bilans-ges.ademe.fr/bilans",
            "Consulter les bilans GES sur la plateforme nationale",
            external=True,
        )

        if not user.is_authenticated:
            return self.calculate_status_for_anonymous_user(
                caracteristiques, primary_action=NON_SOUMIS_PRIMARY_ACTION
            )
        elif not is_user_attached_to_entreprise(user, self.entreprise):
            return self.calculate_status_for_unauthorized_user(caracteristiques)

        if self.est_soumis(caracteristiques):
            status = ReglementationStatus.STATUS_SOUMIS
            status_detail = f"Vous êtes soumis à cette réglementation car {', '.join(self.criteres_remplis(caracteristiques))}."
            primary_action = ReglementationAction(
                "https://bilans-ges.ademe.fr/bilans/comment-publier",
                "Publier mon bilan GES sur la plateforme nationale",
                external=True,
            )
        else:
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation"
            primary_action = NON_SOUMIS_PRIMARY_ACTION
        return ReglementationStatus(
            status, status_detail, primary_action=primary_action
        )
