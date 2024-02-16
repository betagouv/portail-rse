from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation


class CSRDReglementation(Reglementation):
    title = "Rapport de durabilité - Directive CSRD"
    more_info_url = reverse_lazy("reglementations:fiche_csrd")
    tag = "tag-durabilite"
    summary = "Publier un rapport de durabilité"

    @classmethod
    def est_suffisamment_qualifiee(cls, caracteristiques):
        return (
            caracteristiques.entreprise.est_cotee is not None
            and caracteristiques.effectif is not None
            and caracteristiques.tranche_bilan is not None
            and caracteristiques.tranche_chiffre_affaires is not None
            and caracteristiques.entreprise.appartient_groupe is not None
        )

    @classmethod
    def est_soumis(cls, caracteristiques):
        return bool(cls.est_soumis_a_partir_de(caracteristiques))

    @classmethod
    def est_soumis_a_partir_de(
        cls, caracteristiques: CaracteristiquesAnnuelles
    ) -> int | None:
        return 2026


@login_required
def csrd(request):
    return render(
        request,
        "reglementations/espace-csrd.html",
    )
