from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import CategorieJuridique
from entreprises.models import convertit_categorie_juridique
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationStatus


class PlanVigilanceReglementation(Reglementation):
    id = "plan-de-vigilance"
    title = "Plan de vigilance"
    more_info_url = (
        "https://portail-rse.beta.gouv.fr/fiches-reglementaires/plan-de-vigilance/"
    )
    tag = "tag-gouvernance"
    summary = "Établir un plan de vigilance pour prévenir des risques d’atteintes aux droits humains et à l’environnement liés à l'activité des sociétés mères et entreprises donneuses d'ordre."

    @classmethod
    def est_suffisamment_qualifiee(cls, caracteristiques):
        return (
            caracteristiques.effectif is not None
            and caracteristiques.entreprise.appartient_groupe is not None
            and (
                not caracteristiques.entreprise.appartient_groupe
                or (
                    caracteristiques.entreprise.est_societe_mere is not None
                    and caracteristiques.entreprise.societe_mere_en_france is not None
                    and caracteristiques.effectif_groupe is not None
                    and caracteristiques.effectif_groupe_france is not None
                )
            )
        )

    @classmethod
    def critere_categorie_juridique(cls, caracteristiques):
        categorie_juridique = convertit_categorie_juridique(
            caracteristiques.entreprise.categorie_juridique_sirene
        )
        if categorie_juridique in (
            CategorieJuridique.SOCIETE_ANONYME,
            CategorieJuridique.SOCIETE_PAR_ACTIONS_SIMPLIFIEES,
            CategorieJuridique.SOCIETE_COMMANDITE_PAR_ACTIONS,
            CategorieJuridique.SOCIETE_EUROPEENNE,
        ):
            return f"votre entreprise est une {categorie_juridique.label}"
        elif CategorieJuridique.est_une_SA_cooperative(
            caracteristiques.entreprise.categorie_juridique_sirene
        ):
            return "votre entreprise est une Société Anonyme"

    @classmethod
    def critere_effectif(cls, caracteristiques):
        if caracteristiques.effectif in (
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        ):
            return "votre effectif est supérieur à 5 000 salariés"
        elif (
            caracteristiques.entreprise.est_societe_mere
            and caracteristiques.entreprise.societe_mere_en_france
        ):
            if caracteristiques.effectif_groupe_france in (
                CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
            ):
                return "l'effectif du groupe France est supérieur à 5 000 salariés"
            elif caracteristiques.effectif_groupe in (
                CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
            ):
                return (
                    "l'effectif du groupe international est supérieur à 10 000 salariés"
                )

    @classmethod
    def criteres_remplis(cls, caracteristiques):
        criteres = []
        if critere := cls.critere_categorie_juridique(caracteristiques):
            criteres.append(critere)
        if critere := cls.critere_effectif(caracteristiques):
            criteres.append(critere)
        return criteres

    @classmethod
    def est_soumis(cls, caracteristiques):
        super().est_soumis(caracteristiques)
        return len(cls.criteres_remplis(caracteristiques)) >= 2

    @classmethod
    def calculate_status(
        cls,
        caracteristiques: CaracteristiquesAnnuelles,
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(caracteristiques):
            return reglementation_status

        if cls.est_soumis(caracteristiques):
            status = ReglementationStatus.STATUS_SOUMIS
            status_detail = f"Vous êtes soumis à cette réglementation car {' et '.join(cls.criteres_remplis(caracteristiques))}."
            status_detail += " Vous devez établir un plan de vigilance si vous employez, à la clôture de deux exercices consécutifs, au moins 5 000 salariés, en votre sein ou dans vos filiales directes ou indirectes françaises, ou 10 000 salariés, en incluant vos filiales directes ou indirectes étrangères."
        else:
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation."
        return ReglementationStatus(status, status_detail)
