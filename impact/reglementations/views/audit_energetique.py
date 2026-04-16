from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationAction
from reglementations.views.base import ReglementationStatus


class AuditEnergetiqueReglementation(Reglementation):
    id = "audit-energetique"
    title = "Audit énergétique"
    more_info_url = (
        "https://portail-rse.beta.gouv.fr/fiches-reglementaires/audit-energetique/"
    )
    tag = "tag-environnement"
    summary = "Evaluer la performance énergétique de son entreprise."

    @classmethod
    def est_suffisamment_qualifiee(cls, caracteristiques):
        return bool(caracteristiques.tranche_consommation_energie_finale)

    @classmethod
    def criteres_remplis(cls, caracteristiques):
        """Inutile pour l'audit énergétique mais nécessaire car la classe parente a cette classe abstraite"""
        return []

    @classmethod
    def obligation(cls, caracteristiques):
        if (
            caracteristiques.tranche_consommation_energie_finale
            == CaracteristiquesAnnuelles.CONSOMMATION_ENERGIE_ENTRE_2_75GWH_ET_23_6GWH
        ):
            return "L'audit énergétique réglementaire est obligatoire avant le 11 octobre 2026, puis tous les 4 ans."
        elif (
            caracteristiques.tranche_consommation_energie_finale
            == CaracteristiquesAnnuelles.CONSOMMATION_ENERGIE_23_6GWH_ET_PLUS
        ):
            return "Au-dessus de 23,6 GWh/an (85 TJ/an), un système de management de l'énergie certifié ISO 50001 est requis avant le 11 octobre 2027."

    @classmethod
    def est_soumis(cls, caracteristiques):
        super().est_soumis(caracteristiques)
        return caracteristiques.tranche_consommation_energie_finale in (
            CaracteristiquesAnnuelles.CONSOMMATION_ENERGIE_ENTRE_2_75GWH_ET_23_6GWH,
            CaracteristiquesAnnuelles.CONSOMMATION_ENERGIE_23_6GWH_ET_PLUS,
        )

    @classmethod
    def calculate_status(
        cls,
        caracteristiques: CaracteristiquesAnnuelles,
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(caracteristiques):
            return reglementation_status

        if cls.est_soumis(caracteristiques):
            status = ReglementationStatus.STATUS_SOUMIS
            obligation = cls.obligation(caracteristiques)
            status_detail = f"Vous êtes soumis à cette réglementation car votre consommation énergétique est supérieure à 2,75 GWh. {obligation}"
            primary_action = ReglementationAction(
                "https://audit-energie.ademe.fr/",
                "Publier mon audit sur la plateforme nationale",
                external=True,
            )
        else:
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation."
            primary_action = None
        return ReglementationStatus(
            status, status_detail, primary_action=primary_action
        )
