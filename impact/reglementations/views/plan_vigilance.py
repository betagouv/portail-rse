from django.conf import settings

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationStatus


class PlanVigilanceReglementation(Reglementation):
    title = "Plan de vigilance"
    description = """Le plan de vigilance comporte les mesures de vigilance propres à identifier et à prévenir les atteintes graves envers les droits humains et les libertés fondamentales,
        la santé et la sécurité des personnes ainsi que de l’environnement qui adviendraient au sein de l’entreprise."""
    more_info_url = None
    tag = "tag-social"
    summary = ""

    @classmethod
    def est_suffisamment_qualifiee(cls, caracteristiques):
        return (
            caracteristiques.entreprise.categorie_juridique_sirene is not None
            and caracteristiques.effectif is not None
            and caracteristiques.entreprise.appartient_groupe is not None
            and (
                not caracteristiques.entreprise.appartient_groupe
                or caracteristiques.effectif_groupe is not None
            )
        )

    @staticmethod
    def criteres_remplis(caracteristiques):
        criteres = []
        if caracteristiques.effectif in (
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        ):
            criteres.append("votre effectif est supérieur à 5000 salariés")
        elif caracteristiques.effectif_groupe in (
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        ):
            criteres.append("l'effectif du groupe est supérieur à 5000 salariés.")
        return criteres

    @classmethod
    def est_soumis(cls, caracteristiques):
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
            status = ReglementationStatus.STATUS_SOUMIS
            status_detail = f"Vous êtes soumis à cette réglementation car {', '.join(cls.criteres_remplis(caracteristiques))}."
            status_detail += " Vous devez établir un plan de vigilance si vous employez, à la clôture de deux exercices consécutifs, au moins 5 000 salariés, en votre sein ou dans vos filiales directes ou indirectes françaises, ou 10 000 salariés, en incluant vos filiales directes ou indirectes étrangères."
        else:
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation."
        return ReglementationStatus(status, status_detail)
