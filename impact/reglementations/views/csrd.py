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
        if caracteristiques.entreprise.est_cotee:
            if cls.est_grande_entreprise(caracteristiques):
                if caracteristiques.effectif in (
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                    CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                ):
                    return 2025
                else:
                    return 2026
            elif cls.est_petite_ou_moyenne_entreprise(caracteristiques):
                return 2027
        elif cls.est_grande_entreprise(caracteristiques):
            return 2026

    @classmethod
    def est_microentreprise(cls, caracteristiques: CaracteristiquesAnnuelles):
        nombre_seuils_non_depasses = 0
        if (
            caracteristiques.tranche_bilan
            == CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K
        ):
            nombre_seuils_non_depasses += 1
        if (
            caracteristiques.tranche_chiffre_affaires
            == CaracteristiquesAnnuelles.CA_MOINS_DE_700K
        ):
            nombre_seuils_non_depasses += 1
        if caracteristiques.effectif == CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10:
            nombre_seuils_non_depasses += 1
        return nombre_seuils_non_depasses >= 2

    @classmethod
    def est_grande_entreprise(cls, caracteristiques: CaracteristiquesAnnuelles) -> bool:
        nombre_seuils_depasses = 0
        if caracteristiques.tranche_bilan in (
            CaracteristiquesAnnuelles.BILAN_ENTRE_20M_ET_43M,
            CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
            CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        ):
            nombre_seuils_depasses += 1
        if caracteristiques.tranche_chiffre_affaires in (
            CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
            CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
            CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        ):
            nombre_seuils_depasses += 1
        if caracteristiques.effectif in (
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        ):
            nombre_seuils_depasses += 1
        return nombre_seuils_depasses >= 2

    @classmethod
    def est_petite_ou_moyenne_entreprise(
        cls, caracteristiques: CaracteristiquesAnnuelles
    ) -> bool:
        return not cls.est_microentreprise(
            caracteristiques
        ) and not cls.est_grande_entreprise(caracteristiques)


@login_required
def csrd(request):
    return render(
        request,
        "reglementations/espace-csrd.html",
    )
