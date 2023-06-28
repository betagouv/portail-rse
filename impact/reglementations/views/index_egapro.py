from django.conf import settings

from api import egapro
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationAction
from reglementations.views.base import ReglementationStatus


class IndexEgaproReglementation(Reglementation):
    title = "Index de l’égalité professionnelle"
    description = "Afin de lutter contre les inégalités salariales entre les femmes et les hommes, certaines entreprises doivent calculer et transmettre un index mesurant l’égalité salariale au sein de leur structure."
    more_info_url = "https://www.economie.gouv.fr/entreprises/index-egalite-professionnelle-obligatoire"

    def est_soumis(self, caracteristiques):
        return (
            caracteristiques.effectif != CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50
        )

    def calculate_status(
        self,
        caracteristiques: CaracteristiquesAnnuelles,
        user: settings.AUTH_USER_MODEL,
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(caracteristiques, user):
            return reglementation_status

        PRIMARY_ACTION = ReglementationAction(
            "https://egapro.travail.gouv.fr/",
            "Calculer et déclarer mon index sur Egapro",
            external=True,
        )
        if not self.est_soumis(caracteristiques):
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation"
        elif is_index_egapro_published(self.entreprise, caracteristiques.annee):
            status = ReglementationStatus.STATUS_A_JOUR
            status_detail = "Vous êtes soumis à cette réglementation. Vous avez rempli vos obligations d'après les données disponibles sur la plateforme Egapro."
        else:
            status = ReglementationStatus.STATUS_A_ACTUALISER
            status_detail = "Vous êtes soumis à cette réglementation. Vous n'avez pas encore déclaré votre index sur la plateforme Egapro."
        return ReglementationStatus(
            status, status_detail, primary_action=PRIMARY_ACTION
        )


def is_index_egapro_published(entreprise: Entreprise, annee: int) -> bool:
    return egapro.is_index_egapro_published(entreprise.siren, annee)
