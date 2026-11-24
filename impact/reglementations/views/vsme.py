from datetime import date

from django.urls.base import reverse_lazy

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationAction
from reglementations.views.base import ReglementationStatus

class VSMEReglementation(Reglementation):
    id = "vsme"
    title = "Standard volontaire européen - VS (ex-VSME)"
    more_info_url = "https://portail-rse.beta.gouv.fr/fiches-reglementaires/norme-volontaire-de-durabilite-vsme/"
    tag = "tag-durabilite"
    summary = ""
    zone = "europe"

    @classmethod
    def est_suffisamment_qualifiee(cls, caracteristiques):
        return True

    @classmethod
    def criteres_remplis(cls, caracteristiques):
        return []

    @classmethod
    def est_soumis(cls, caracteristiques):
        return False

    @classmethod
    def calculate_status(
        cls,
        caracteristiques: CaracteristiquesAnnuelles,
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(caracteristiques):
            return reglementation_status

        primary_action = ReglementationAction(
            reverse_lazy(
                "vsme:categories_vsme",
                kwargs={
                    "id_public": caracteristiques.entreprise.id_public,
                    "annee": date.today().year - 1,
                },
            ),
            "Remplir mes indicateurs VS (ex-VSME)",
        )

        secondary_actions = [
            ReglementationAction(
                reverse_lazy(
                    "vsme:etape_vsme",
                    kwargs={
                        "id_public": caracteristiques.entreprise.id_public,
                        "etape": "introduction",
                    },
                ),
                "Découvrir la démarche VS (ex-VSME)",
            )
        ]

        return ReglementationStatus(
            status=ReglementationStatus.STATUS_RECOMMANDE,
            status_detail="""Cette norme est volontaire et recommandée pour les entreprises qui souhaitent mieux structurer leurs informations de durabilité et identifier un plafond d'informations à communiquer aux entreprises soumises à la CSRD ("value chain cap").""",
            primary_action=primary_action,
            secondary_actions=secondary_actions,
        )
