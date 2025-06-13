from django.conf import settings
from django.urls.base import reverse_lazy

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationAction
from reglementations.views.base import ReglementationStatus


"""
utils:
- Module très mal nommé en attendant de réorganiser la structure de l'app `reglementations`
- contient pour l'instant les différentes classes ou fonctions utilitaires pour les VSME
"""

# Modèles non-ORM :
# Les modèles de traitement des réglementations (non-ORM),
# devraient être situés "proches" des réglementations concernées.
# Difficile dans le cas des VSME (import cyclique).
# A moyen|long-terme, ces classes utilitaires devraient être placées ailleurs
# que dans les vues (et probablement dans une autre app ou package).


# TODO: à complèter et adapter après discussion
class VSMEReglementation(Reglementation):
    title = "Standard volontaire européen - VSME"
    more_info_url = "https://portail-rse.beta.gouv.fr/csrd/vsme-pme/"
    tag = "tag-social"
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
        user: settings.AUTH_USER_MODEL,
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(caracteristiques, user):
            return reglementation_status

        primary_action = ReglementationAction(
            reverse_lazy(
                "vsme:etape_vsme",
                kwargs={
                    "siren": caracteristiques.entreprise.siren,
                    "etape": "introduction",
                },
            ),
            "Découvrir la démarche VSME",
        )

        return ReglementationStatus(
            status=ReglementationStatus.STATUS_RECOMMANDE,
            status_detail="Cette norme est volontaire et recommandée pour les entreprises qui souhaitent mieux structurer leurs informations de durabilité.",
            primary_action=primary_action,
        )
