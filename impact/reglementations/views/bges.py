from datetime import date

from api import bges
from api.exceptions import APIError
from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationAction
from reglementations.views.base import ReglementationStatus


class BGESReglementation(Reglementation):
    title = "BEGES et Plan de Transition"
    more_info_url = "https://portail-rse.beta.gouv.fr/fiches-reglementaires/bilan-eges-et-plan-de-transition/"
    tag = "tag-environnement"
    summary = "Mesurer ses émissions de gaz à effet de serre directes et adopter un plan de transition en conséquence."

    CONSULTER_BILANS_PRIMARY_ACTION = ReglementationAction(
        "https://bilans-ges.ademe.fr/bilans",
        "Consulter les bilans GES sur la plateforme nationale",
        external=True,
    )
    PUBLIER_BILAN_PRIMARY_ACTION = ReglementationAction(
        "https://bilans-ges.ademe.fr/bilans/comment-publier",
        "Publier mon bilan GES sur la plateforme nationale",
        external=True,
    )

    @classmethod
    def est_suffisamment_qualifiee(cls, caracteristiques):
        return (
            caracteristiques.effectif is not None
            and caracteristiques.effectif_outre_mer is not None
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

        if (
            caracteristiques.effectif_outre_mer
            == CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_250_ET_PLUS
        ):
            criteres.append("votre effectif outre-mer est supérieur à 250 salariés")
        return criteres

    @classmethod
    def est_soumis(cls, caracteristiques):
        super().est_soumis(caracteristiques)
        return bool(cls.criteres_remplis(caracteristiques))

    @classmethod
    def calculate_status(
        cls,
        caracteristiques: CaracteristiquesAnnuelles,
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(caracteristiques):
            return reglementation_status

        if cls.est_soumis(caracteristiques):
            status_detail = f"Vous êtes soumis à cette réglementation car {', '.join(cls.criteres_remplis(caracteristiques))}."
            try:
                annee_reporting = bges.last_reporting_year(
                    caracteristiques.entreprise.siren
                )
            except APIError:
                status = ReglementationStatus.STATUS_SOUMIS
                primary_action = cls.PUBLIER_BILAN_PRIMARY_ACTION
                status_detail += " Suite à un problème technique, les informations concernant votre dernière publication n'ont pas pu être récupérées sur la plateforme Bilans GES. Vérifiez que vous avez publié votre bilan il y a moins de 4 ans."
                return ReglementationStatus(
                    status, status_detail, primary_action=primary_action
                )

            if not annee_reporting:
                status = ReglementationStatus.STATUS_A_ACTUALISER
                primary_action = cls.PUBLIER_BILAN_PRIMARY_ACTION
                status_detail += " Vous n'avez pas encore publié votre bilan sur la plateforme Bilans GES."
            elif not cls.publication_est_recente(annee_reporting):
                status = ReglementationStatus.STATUS_A_ACTUALISER
                primary_action = cls.PUBLIER_BILAN_PRIMARY_ACTION
                status_detail += f" Le dernier bilan publié sur la plateforme Bilans GES concerne l'année {annee_reporting}."
            else:
                status = ReglementationStatus.STATUS_A_JOUR
                primary_action = cls.CONSULTER_BILANS_PRIMARY_ACTION
                status_detail += f" Vous avez publié un bilan {annee_reporting} sur la plateforme Bilans GES."
        else:
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation."
            primary_action = cls.CONSULTER_BILANS_PRIMARY_ACTION
        return ReglementationStatus(
            status, status_detail, primary_action=primary_action
        )

    @classmethod
    def publication_est_recente(cls, annee_reporting):
        """une entreprise doit publier son bilan GES tous les quatre ans"""
        DELAI_MAX_PUBLICATION = 4
        annee_en_cours = date.today().year
        return annee_en_cours - annee_reporting < DELAI_MAX_PUBLICATION
