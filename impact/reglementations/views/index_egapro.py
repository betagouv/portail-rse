from django.conf import settings
from django.urls import reverse_lazy

from api import egapro
from entreprises.models import CaracteristiquesAnnuelles
from reglementations.models import derniere_annee_a_publier_index_egapro
from reglementations.models import prochaine_echeance_index_egapro
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationAction
from reglementations.views.base import ReglementationStatus


class IndexEgaproReglementation(Reglementation):
    title = "Index de l’égalité professionnelle"
    description = "Afin de lutter contre les inégalités salariales entre les femmes et les hommes, certaines entreprises doivent calculer et transmettre un index mesurant l’égalité salariale au sein de leur structure."
    more_info_url = reverse_lazy("reglementations:fiche_index_egapro")
    tag = "tag-social"
    summary = "Mesurer les écarts de rémunération entre les femmes et les hommes au sein de son entreprise."
    NON_SOUMIS_PRIMARY_ACTION = ReglementationAction(
        "https://egapro.travail.gouv.fr/index-egapro/recherche",
        "Consulter les index sur la plateforme nationale",
        external=True,
    )

    @classmethod
    def est_suffisamment_qualifiee(cls, caracteristiques):
        return caracteristiques.effectif is not None

    @classmethod
    def est_soumis(cls, caracteristiques):
        super().est_soumis(caracteristiques)
        return (
            caracteristiques.effectif != CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50
        )

    @classmethod
    def calculate_status(
        cls,
        caracteristiques: CaracteristiquesAnnuelles,
        user: settings.AUTH_USER_MODEL,
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(caracteristiques, user):
            return reglementation_status

        if not cls.est_soumis(caracteristiques):
            return ReglementationStatus(
                status=ReglementationStatus.STATUS_NON_SOUMIS,
                status_detail="Vous n'êtes pas soumis à cette réglementation.",
                primary_action=cls.NON_SOUMIS_PRIMARY_ACTION,
            )
        else:
            primary_action = ReglementationAction(
                "https://egapro.travail.gouv.fr/",
                "Publier mon index sur la plateforme nationale",
                external=True,
            )
            annee = derniere_annee_a_publier_index_egapro()
            derniere_annee_est_publiee = egapro.is_index_egapro_published(
                caracteristiques.entreprise.siren, annee
            )
            if derniere_annee_est_publiee:
                status = ReglementationStatus.STATUS_A_JOUR
                status_detail = f"Vous êtes soumis à cette réglementation car votre effectif est supérieur à 50 salariés. Vous avez publié votre index {annee} d'après les données disponibles sur la plateforme Egapro."
            else:
                status = ReglementationStatus.STATUS_A_ACTUALISER
                status_detail = f"Vous êtes soumis à cette réglementation car votre effectif est supérieur à 50 salariés. Vous n'avez pas encore publié votre index {annee} sur la plateforme Egapro. Vous devez calculer et publier votre index chaque année au plus tard le 1er mars."
            return ReglementationStatus(
                status,
                status_detail,
                prochaine_echeance=prochaine_echeance_index_egapro(
                    derniere_annee_est_publiee
                ).strftime("%d/%m/%Y"),
                primary_action=primary_action,
            )

    @classmethod
    def calculate_status_for_anonymous_user(
        cls, caracteristiques: CaracteristiquesAnnuelles
    ):
        return super().calculate_status_for_anonymous_user(
            caracteristiques, primary_action=cls.NON_SOUMIS_PRIMARY_ACTION
        )
