from django.conf import settings
from django.urls import reverse_lazy

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import CategorieJuridique
from entreprises.models import convertit_categorie_juridique
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationStatus


class DPEFReglementation(Reglementation):
    title = "Déclaration de Performance Extra-Financière"
    more_info_url = reverse_lazy("reglementations:fiche_dpef")
    tag = "tag-durabilite"
    summary = "Établir une déclaration de performance extra-financière contenant des informations sociales, environnementales et sociétales."

    CRITERE_EFFECTIF_PERMANENT = "votre effectif permanent est supérieur à 500 salariés"
    CRITERE_EFFECTIF_GROUPE_PERMANENT = (
        "l'effectif permanent du groupe est supérieur à 500 salariés"
    )

    @classmethod
    def est_suffisamment_qualifiee(cls, caracteristiques):
        return (
            caracteristiques.entreprise.est_cotee is not None
            and caracteristiques.effectif_permanent is not None
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
                            caracteristiques.effectif_groupe_permanent is not None
                            and caracteristiques.tranche_bilan_consolide is not None
                            and caracteristiques.tranche_chiffre_affaires_consolide
                            is not None
                        )
                    )
                )
            )
        )

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
            criteres = cls.criteres_remplis(caracteristiques)
            justification = ", ".join(criteres[:-1]) + " et " + criteres[-1]
            status_detail = (
                f"Vous êtes soumis à cette réglementation car {justification}."
            )
        else:
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation."
        return ReglementationStatus(status, status_detail)

    @classmethod
    def criteres_remplis(cls, caracteristiques):
        criteres = []
        categorie_juridique = convertit_categorie_juridique(
            caracteristiques.entreprise.categorie_juridique_sirene
        )
        criteres.append(f"votre entreprise est une {categorie_juridique.label}")
        if critere := cls.critere_effectif(caracteristiques):
            criteres.append(critere)
        if categorie_juridique in (
            CategorieJuridique.INSTITUTION_PREVOYANCE,
            CategorieJuridique.MUTUELLE,
            CategorieJuridique.SOCIETE_COOPERATIVE_AGRICOLE,
            CategorieJuridique.SOCIETE_COOPERATIVE_DE_PRODUCTION,
        ):
            if critere := cls.critere_bilan_non_cotee(caracteristiques):
                criteres.append(critere)
            if critere := cls.critere_chiffre_affaires_non_cotee(caracteristiques):
                criteres.append(critere)
        elif categorie_juridique == CategorieJuridique.SOCIETE_ASSURANCE_MUTUELLE:
            if critere := cls.critere_bilan_cotee(caracteristiques):
                criteres.append(critere)
            if critere := cls.critere_chiffre_affaires_cotee(caracteristiques):
                criteres.append(critere)
        elif categorie_juridique in (
            CategorieJuridique.SOCIETE_ANONYME,
            CategorieJuridique.SOCIETE_COMMANDITE_PAR_ACTIONS,
            CategorieJuridique.SOCIETE_EUROPEENNE,
        ):
            if caracteristiques.entreprise.est_cotee:
                criteres.append(f"votre société est cotée sur un marché réglementé")
                if critere := cls.critere_bilan_cotee(caracteristiques):
                    criteres.append(critere)
                if critere := cls.critere_chiffre_affaires_cotee(caracteristiques):
                    criteres.append(critere)
            else:
                if critere := cls.critere_bilan_non_cotee(caracteristiques):
                    criteres.append(critere)
                if critere := cls.critere_chiffre_affaires_non_cotee(caracteristiques):
                    criteres.append(critere)
        return criteres

    @classmethod
    def critere_effectif(cls, caracteristiques):
        TRANCHES_ACCEPTEES = (
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        )
        if caracteristiques.effectif_permanent in TRANCHES_ACCEPTEES:
            return cls.CRITERE_EFFECTIF_PERMANENT
        elif (
            caracteristiques.entreprise.comptes_consolides
            and caracteristiques.effectif_groupe_permanent in TRANCHES_ACCEPTEES
        ):
            return cls.CRITERE_EFFECTIF_GROUPE_PERMANENT

    @classmethod
    def critere_bilan_cotee(cls, caracteristiques):
        if caracteristiques.tranche_bilan in (
            CaracteristiquesAnnuelles.BILAN_ENTRE_25M_ET_43M,
            CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
            CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        ):
            return "votre bilan est supérieur à 20M€"
        elif caracteristiques.tranche_bilan_consolide in (
            CaracteristiquesAnnuelles.BILAN_ENTRE_30M_ET_43M,
            CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
            CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        ):
            return "votre bilan consolidé est supérieur à 20M€"

    @classmethod
    def critere_chiffre_affaires_cotee(cls, caracteristiques):
        if caracteristiques.tranche_chiffre_affaires in (
            CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
            CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        ):
            return "votre chiffre d'affaires est supérieur à 40M€"
        elif caracteristiques.tranche_chiffre_affaires_consolide in (
            CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
            CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        ):
            return "votre chiffre d'affaires consolidé est supérieur à 40M€"

    @classmethod
    def critere_bilan_non_cotee(cls, caracteristiques):
        if (
            caracteristiques.tranche_bilan
            == CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS
        ):
            return "votre bilan est supérieur à 100M€"
        elif (
            caracteristiques.tranche_bilan_consolide
            == CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS
        ):
            return "votre bilan consolidé est supérieur à 100M€"

    @classmethod
    def critere_chiffre_affaires_non_cotee(cls, caracteristiques):
        if (
            caracteristiques.tranche_chiffre_affaires
            == CaracteristiquesAnnuelles.CA_100M_ET_PLUS
        ):
            return "votre chiffre d'affaires est supérieur à 100M€"
        elif (
            caracteristiques.tranche_chiffre_affaires_consolide
            == CaracteristiquesAnnuelles.CA_100M_ET_PLUS
        ):
            return "votre chiffre d'affaires consolidé est supérieur à 100M€"

    @classmethod
    def est_soumis(cls, caracteristiques):
        super().est_soumis(caracteristiques)
        categorie_juridique = convertit_categorie_juridique(
            caracteristiques.entreprise.categorie_juridique_sirene
        )
        if categorie_juridique in (
            CategorieJuridique.INSTITUTION_PREVOYANCE,
            CategorieJuridique.MUTUELLE,
            CategorieJuridique.SOCIETE_COOPERATIVE_AGRICOLE,
            CategorieJuridique.SOCIETE_COOPERATIVE_DE_PRODUCTION,
        ):
            return cls.est_soumis_non_cotee(caracteristiques)
        elif categorie_juridique == CategorieJuridique.SOCIETE_ASSURANCE_MUTUELLE:
            return cls.est_soumis_cotee(caracteristiques)
        elif categorie_juridique in (
            CategorieJuridique.SOCIETE_ANONYME,
            CategorieJuridique.SOCIETE_COMMANDITE_PAR_ACTIONS,
            CategorieJuridique.SOCIETE_EUROPEENNE,
        ):
            if caracteristiques.entreprise.est_cotee:
                return cls.est_soumis_cotee(caracteristiques)
            else:
                return cls.est_soumis_non_cotee(caracteristiques)

    @classmethod
    def est_soumis_non_cotee(cls, caracteristiques):
        return cls.critere_effectif(caracteristiques) and (
            cls.critere_bilan_non_cotee(caracteristiques)
            or cls.critere_chiffre_affaires_non_cotee(caracteristiques)
        )

    @classmethod
    def est_soumis_cotee(cls, caracteristiques):
        return cls.critere_effectif(caracteristiques) and (
            cls.critere_bilan_cotee(caracteristiques)
            or cls.critere_chiffre_affaires_cotee(caracteristiques)
        )
