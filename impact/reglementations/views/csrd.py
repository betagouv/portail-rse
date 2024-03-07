from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationAction
from reglementations.views.base import ReglementationStatus


class CSRDReglementation(Reglementation):
    title = "Rapport de Durabilité - CSRD"
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
            and (
                not caracteristiques.entreprise.appartient_groupe
                or (
                    caracteristiques.entreprise.comptes_consolides is not None
                    and (
                        not caracteristiques.entreprise.comptes_consolides
                        or (
                            caracteristiques.effectif_groupe is not None
                            and caracteristiques.tranche_bilan_consolide is not None
                            and caracteristiques.tranche_chiffre_affaires_consolide
                            is not None
                        )
                    )
                )
            )
        )

    @classmethod
    def est_soumis(cls, caracteristiques):
        super().est_soumis(caracteristiques)
        return bool(cls.est_soumis_a_partir_de(caracteristiques))

    @classmethod
    def est_soumis_a_partir_de(
        cls, caracteristiques: CaracteristiquesAnnuelles
    ) -> int | None:
        if cls.est_grand_groupe(caracteristiques):
            if caracteristiques.entreprise.est_societe_mere:
                if (
                    caracteristiques.entreprise.est_cotee
                    and caracteristiques.effectif_groupe
                    in (
                        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                    )
                ):
                    return 2025
                else:
                    return 2026
            else:
                if cls.est_grande_entreprise(caracteristiques):
                    if (
                        caracteristiques.entreprise.est_cotee
                        and caracteristiques.effectif
                        in (
                            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                        )
                    ):
                        return 2025
                    else:
                        return 2026
                elif (
                    caracteristiques.entreprise.est_cotee
                    and cls.est_petite_ou_moyenne_entreprise(caracteristiques)
                ):
                    if caracteristiques.effectif_groupe in (
                        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                    ):
                        return 2025
                    else:
                        return 2026
        else:
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
    def criteres_remplis(cls, caracteristiques):
        criteres = []
        if caracteristiques.entreprise.est_cotee:
            criteres.append("votre société est cotée sur un marché réglementé")
        if caracteristiques.entreprise.est_societe_mere and cls.est_grand_groupe(
            caracteristiques
        ):
            criteres.append("votre société est la société mère d'un groupe")
        if critere := cls.critere_effectif(caracteristiques):
            criteres.append(critere)
        if critere := cls.critere_bilan(caracteristiques):
            criteres.append(critere)
        if critere := cls.critere_CA(caracteristiques):
            criteres.append(critere)
        return criteres

    @classmethod
    def critere_effectif(cls, caracteristiques):
        if caracteristiques.entreprise.est_cotee:
            if cls.est_grande_entreprise(caracteristiques):
                if caracteristiques.effectif in (
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                    CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                ):
                    return "votre effectif est supérieur à 500 salariés"
                elif caracteristiques.effectif in (
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
                ):
                    return "votre effectif est supérieur à 250 salariés"
            if cls.est_grand_groupe(caracteristiques):
                if caracteristiques.effectif_groupe in (
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                    CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                ):
                    return "l'effectif du groupe est supérieur à 500 salariés"
                elif (
                    caracteristiques.effectif_groupe
                    == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499
                ):
                    return "l'effectif du groupe est supérieur à 250 salariés"
            if cls.est_petite_ou_moyenne_entreprise(caracteristiques):
                if (
                    caracteristiques.effectif
                    != CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10
                ):
                    return "votre effectif est supérieur à 10 salariés"
        else:
            if cls.est_grande_entreprise(caracteristiques):
                if caracteristiques.effectif in (
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                    CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                ):
                    return "votre effectif est supérieur à 250 salariés"
            if caracteristiques.entreprise.est_societe_mere and cls.est_grand_groupe(
                caracteristiques
            ):
                if caracteristiques.effectif_groupe in (
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                    CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                ):
                    return "l'effectif du groupe est supérieur à 250 salariés"

    @classmethod
    def critere_bilan(cls, caracteristiques):
        if cls.est_grand_groupe(caracteristiques):
            if caracteristiques.tranche_bilan_consolide in (
                CaracteristiquesAnnuelles.BILAN_ENTRE_30M_ET_43M,
                CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
                CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
            ):
                return "le bilan du groupe est supérieur à 30M€"
        if caracteristiques.tranche_bilan in (
            CaracteristiquesAnnuelles.BILAN_ENTRE_20M_ET_43M,
            CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
            CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        ):
            if cls.est_grande_entreprise(caracteristiques):
                return "votre bilan est supérieur à 20M€"
            elif cls.est_petite_ou_moyenne_entreprise(caracteristiques):
                return "votre bilan est supérieur à 350k€"
        elif caracteristiques.tranche_bilan in (
            CaracteristiquesAnnuelles.BILAN_ENTRE_350K_ET_6M,
            CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        ):
            if cls.est_petite_ou_moyenne_entreprise(caracteristiques):
                return "votre bilan est supérieur à 350k€"

    @classmethod
    def critere_CA(cls, caracteristiques):
        if cls.est_grand_groupe(caracteristiques):
            if caracteristiques.tranche_chiffre_affaires_consolide in (
                CaracteristiquesAnnuelles.CA_ENTRE_60M_ET_100M,
                CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
            ):
                return "le chiffre d'affaires du groupe est supérieur à 60M€"
        if caracteristiques.tranche_chiffre_affaires in (
            CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
            CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
            CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        ):
            if cls.est_grande_entreprise(caracteristiques):
                return "votre chiffre d'affaires est supérieur à 40M€"
            elif cls.est_petite_ou_moyenne_entreprise(caracteristiques):
                return "votre chiffre d'affaires est supérieur à 700k€"
        elif caracteristiques.tranche_chiffre_affaires in (
            CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
            CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
        ):
            if cls.est_petite_ou_moyenne_entreprise(caracteristiques):
                return "votre chiffre d'affaires est supérieur à 700k€"

    @classmethod
    def calculate_status(
        cls,
        caracteristiques: CaracteristiquesAnnuelles,
        user: settings.AUTH_USER_MODEL,
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(caracteristiques, user):
            return reglementation_status
        primary_action = ReglementationAction(
            reverse_lazy("reglementations:csrd"),
            "Accéder à l'espace Rapport de Durabilité",
        )
        if annee := cls.est_soumis_a_partir_de(caracteristiques):
            criteres = cls.criteres_remplis(caracteristiques)
            justification = ", ".join(criteres[:-1]) + " et " + criteres[-1]
            return ReglementationStatus(
                status=ReglementationStatus.STATUS_SOUMIS,
                status_detail=f"Vous êtes soumis à cette réglementation à partir de {annee} sur les données de {annee - 1} car {justification}.",
                primary_action=primary_action,
                prochaine_echeance=annee,
            )
        else:
            return ReglementationStatus(
                status=ReglementationStatus.STATUS_NON_SOUMIS,
                status_detail="Vous n'êtes pas soumis à cette réglementation.",
                primary_action=primary_action,
            )

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

    @classmethod
    def est_grand_groupe(cls, caracteristiques: CaracteristiquesAnnuelles) -> bool:
        nombre_seuils_depasses = 0
        if caracteristiques.tranche_bilan_consolide in (
            CaracteristiquesAnnuelles.BILAN_ENTRE_30M_ET_43M,
            CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
            CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        ):
            nombre_seuils_depasses += 1
        if caracteristiques.tranche_chiffre_affaires_consolide in (
            CaracteristiquesAnnuelles.CA_ENTRE_60M_ET_100M,
            CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        ):
            nombre_seuils_depasses += 1
        if caracteristiques.effectif_groupe in (
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        ):
            nombre_seuils_depasses += 1
        return (
            caracteristiques.entreprise.appartient_groupe
            and nombre_seuils_depasses >= 2
        )


@login_required
def csrd(request):
    return render(
        request,
        "reglementations/espace-csrd.html",
    )
