from django.conf import settings

from api import egapro
from api.exceptions import APIError
from entreprises.models import CaracteristiquesAnnuelles
from reglementations.models import derniere_annee_a_publier_index_egapro
from reglementations.models import prochaine_echeance_index_egapro
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationAction
from reglementations.views.base import ReglementationStatus


class IndexEgaproReglementation(Reglementation):
    title = "Index de l’égalité professionnelle"
    more_info_url = "https://portail-rse.beta.gouv.fr/fiches-reglementaires/index-egalite-professionnelle/"
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

        if not cls.est_soumis(caracteristiques):
            return ReglementationStatus(
                status=ReglementationStatus.STATUS_NON_SOUMIS,
                status_detail="Vous n'êtes pas soumis à cette norme.",
                primary_action=cls.NON_SOUMIS_PRIMARY_ACTION,
            )
        else:
            primary_action = ReglementationAction(
                "https://egapro.travail.gouv.fr/",
                "Publier mon index sur la plateforme nationale",
                external=True,
            )
            annee = derniere_annee_a_publier_index_egapro()
            try:
                derniere_annee_est_publiee = egapro.is_index_egapro_published(
                    caracteristiques.entreprise.siren, annee
                )
            except APIError:
                return ReglementationStatus(
                    ReglementationStatus.STATUS_SOUMIS,
                    f"Vous êtes soumis à cette norme car {', '.join(cls.criteres_remplis(caracteristiques))}. Suite à un problème technique, les informations concernant votre dernière publication n'ont pas pu être récupérées sur la plateforme EgaPro. Vous devez calculer et publier votre index chaque année au plus tard le 1er mars.",
                    primary_action=primary_action,
                )
            if derniere_annee_est_publiee:
                status = ReglementationStatus.STATUS_A_JOUR
                status_detail = f"Vous êtes soumis à cette norme car {', '.join(cls.criteres_remplis(caracteristiques))}. Vous avez publié votre index {annee} d'après les données disponibles sur la plateforme Egapro."
            else:
                status = ReglementationStatus.STATUS_A_ACTUALISER
                status_detail = f"Vous êtes soumis à cette norme car {', '.join(cls.criteres_remplis(caracteristiques))}. Vous n'avez pas encore publié votre index {annee} sur la plateforme Egapro. Vous devez calculer et publier votre index chaque année au plus tard le 1er mars."
            return ReglementationStatus(
                status,
                status_detail,
                prochaine_echeance=prochaine_echeance_index_egapro(
                    derniere_annee_est_publiee
                ).strftime("%d/%m/%Y"),
                primary_action=primary_action,
            )
