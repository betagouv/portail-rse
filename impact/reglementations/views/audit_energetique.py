from django.conf import settings

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationAction
from reglementations.views.base import ReglementationStatus


class AuditEnergetiqueReglementation(Reglementation):
    title = "Audit énergétique"
    description = "Le code de l'énergie prévoit la réalisation d’un audit énergétique pour les grandes entreprises de plus de 250 salariés, afin qu’elles mettent en place une stratégie d’efficacité énergétique de leurs activités. L’audit énergétique permet de repérer les gisements d’économies d’énergie chez les plus gros consommateurs professionnels (tertiaires et industriels). L’audit doit dater de moins de 4 ans."
    more_info_url = (
        "https://www.ecologie.gouv.fr/audit-energetique-des-grandes-entreprises"
    )

    def criteres_remplis(self, caracteristiques):
        criteres = []
        if caracteristiques.effectif in (
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
            CaracteristiquesAnnuelles.EFFECTIF_500_ET_PLUS,
        ):
            criteres.append("votre effectif est supérieur à 250 salariés")

        if caracteristiques.tranche_chiffre_affaires in (
            CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
            CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        ):
            if caracteristiques.tranche_bilan in (
                CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
                CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
            ):
                criteres.append(
                    "votre bilan est supérieur à 43M€ et votre chiffre d'affaires est supérieur à 50M€"
                )
            elif caracteristiques.tranche_bilan_consolide in (
                CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
                CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
            ):
                criteres.append(
                    "votre bilan consolidé est supérieur à 43M€ et votre chiffre d'affaires est supérieur à 50M€"
                )
        return criteres

    def est_soumis(self, caracteristiques):
        return (
            not caracteristiques.systeme_management_energie
        ) and self.criteres_remplis(caracteristiques)

    def calculate_status(
        self,
        caracteristiques: CaracteristiquesAnnuelles,
        user: settings.AUTH_USER_MODEL,
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(caracteristiques, user):
            return reglementation_status

        if self.est_soumis(caracteristiques):
            status = ReglementationStatus.STATUS_SOUMIS
            status_detail = f"Vous êtes soumis à cette réglementation car {', '.join(self.criteres_remplis(caracteristiques))}."
            status_detail += " Vous devez réaliser un audit énergétique si vous remplissez l'une des conditions suivantes lors des deux derniers exercices comptables : soit votre effectif est supérieur à 250 salariés, soit votre bilan (ou bilan consolidé) est supérieur à 43M€ et votre chiffre d'affaires est supérieur à 50M€."
            primary_action = ReglementationAction(
                "https://audit-energie.ademe.fr/",
                "Publier mon audit",
                external=True,
            )
        else:
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation"
            if caracteristiques.systeme_management_energie:
                status_detail += " si le système de management de l'énergie est certifié par un organisme de certification accrédité par un organisme d'accréditation signataire de l'accord de reconnaissance multilatéral établi par la coordination européenne des organismes d'accréditation et que ce système prévoit un audit énergétique satisfaisant aux critères mentionnés à l'article L. 233-1."
            else:
                status_detail += "."
            primary_action = None
        return ReglementationStatus(status, status_detail, primary_action)
