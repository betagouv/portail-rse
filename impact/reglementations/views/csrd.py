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
        if cls.est_microentreprise(caracteristiques):
            return None
        if caracteristiques.entreprise.est_cotee:
            if caracteristiques.effectif in (
                CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
            ):
                return 2025
        return 2026

    @classmethod
    def est_microentreprise(cls, caracteristiques: CaracteristiquesAnnuelles):
        score = 0
        if (
            caracteristiques.tranche_bilan
            == CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K
        ):
            score += 1
        if (
            caracteristiques.tranche_chiffre_affaires
            == CaracteristiquesAnnuelles.CA_MOINS_DE_700K
        ):
            score += 1
        if caracteristiques.effectif == CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50:
            score += 1
        return score >= 2


@login_required
def csrd(request):
    return render(
        request,
        "reglementations/espace-csrd.html",
    )
