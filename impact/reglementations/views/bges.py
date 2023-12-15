from datetime import date

from django.conf import settings
from django.urls import reverse_lazy

from api import bges
from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationAction
from reglementations.views.base import ReglementationStatus


class BGESReglementation(Reglementation):
    title = "BGES et plan de transition"
    description = "Le bilan GES réglementaire a vocation à contribuer à la mise en œuvre de la stratégie de réduction des émissions de GES des entreprises. Un plan de transition est obligatoirement joint à ce bilan. Il vise à réduire les émissions de gaz à effet de serre et présente les objectifs, moyens et actions envisagées à cette fin ainsi que, le cas échéant, les actions mises en œuvre lors du précédent bilan. Ils sont mis à jour tous les quatre ans."
    more_info_url = reverse_lazy("reglementations:fiche_bilan_ges")
    tag = "tag-environnement"
    summary = "Mesurer ses émissions de gaz à effet de serre directes et adopter un plan de transition en conséquence."
    NON_SOUMIS_PRIMARY_ACTION = ReglementationAction(
        "https://bilans-ges.ademe.fr/bilans",
        "Consulter les bilans GES sur la plateforme nationale",
        external=True,
    )

    @classmethod
    def est_suffisamment_qualifiee(cls, caracteristiques):
        return (
            caracteristiques.effectif is not None
            and caracteristiques.effectif_outre_mer is not None
        )

    @staticmethod
    def criteres_remplis(caracteristiques):
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
        return cls.criteres_remplis(caracteristiques)

    @classmethod
    def calculate_status(
        cls,
        caracteristiques: CaracteristiquesAnnuelles,
        user: settings.AUTH_USER_MODEL,
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(caracteristiques, user):
            return reglementation_status

        if cls.est_soumis(caracteristiques):
            annee_publication = bges.bges_publication_year(caracteristiques.annee)
            if annee_publication and cls.publication_est_recente(annee_publication):
                status = ReglementationStatus.STATUS_A_JOUR
                primary_action = ReglementationAction(
                    "https://bilans-ges.ademe.fr",
                    "Voir les bilans GES sur la plateforme nationale",
                    external=True,
                )
            else:
                status = ReglementationStatus.STATUS_A_ACTUALISER
                primary_action = ReglementationAction(
                    "https://bilans-ges.ademe.fr/bilans/comment-publier",
                    "Publier mon bilan GES sur la plateforme nationale",
                    external=True,
                )
            status_detail = f"Vous êtes soumis à cette réglementation car {', '.join(cls.criteres_remplis(caracteristiques))}."
        else:
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation"
            primary_action = cls.NON_SOUMIS_PRIMARY_ACTION
        return ReglementationStatus(
            status, status_detail, primary_action=primary_action
        )

    @classmethod
    def calculate_status_for_anonymous_user(
        cls, caracteristiques: CaracteristiquesAnnuelles
    ):
        return super().calculate_status_for_anonymous_user(
            caracteristiques, primary_action=cls.NON_SOUMIS_PRIMARY_ACTION
        )

    @classmethod
    def publication_est_recente(cls, annee_publication):
        """une entreprise doit publier son bilan GES tous les quatre ans"""
        DELAI_MAX_PUBLICATION = 4
        annee_en_cours = date.today().year
        return annee_en_cours - annee_publication < DELAI_MAX_PUBLICATION
