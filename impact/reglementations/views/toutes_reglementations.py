from entreprises.models import CaracteristiquesAnnuelles
from reglementations.utils import VSMEReglementation
from reglementations.views.audit_energetique import AuditEnergetiqueReglementation
from reglementations.views.base import ReglementationStatus
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.bges import BGESReglementation
from reglementations.views.csrd import CSRDReglementation
from reglementations.views.dispositif_alerte import DispositifAlerteReglementation
from reglementations.views.dispositif_anticorruption import DispositifAntiCorruption
from reglementations.views.index_egapro import IndexEgaproReglementation
from reglementations.views.plan_vigilance import PlanVigilanceReglementation

REGLEMENTATIONS = [
    VSMEReglementation,
    CSRDReglementation,
    BDESEReglementation,
    IndexEgaproReglementation,
    DispositifAlerteReglementation,
    BGESReglementation,
    AuditEnergetiqueReglementation,
    DispositifAntiCorruption,
    PlanVigilanceReglementation,
]


def calcule_reglementations(caracteristiques: CaracteristiquesAnnuelles):
    reglementations = [
        {
            "reglementation": reglementation,
            "status": reglementation.calculate_status(caracteristiques),
        }
        for reglementation in REGLEMENTATIONS
    ]
    return reglementations


def etats_reglementations_selon_caracteristiques(caracteristiques):
    reglementations = calcule_reglementations(caracteristiques)
    reglementations_a_actualiser = [
        r
        for r in reglementations
        if r["status"].status == ReglementationStatus.STATUS_A_ACTUALISER
    ]
    reglementations_en_cours = [
        r
        for r in reglementations
        if r["status"].status == ReglementationStatus.STATUS_EN_COURS
    ]
    reglementations_a_jour = [
        r
        for r in reglementations
        if r["status"].status == ReglementationStatus.STATUS_A_JOUR
    ]
    reglementations_soumises = [
        r
        for r in reglementations
        if r["status"].status == ReglementationStatus.STATUS_SOUMIS
    ]
    reglementations_non_soumises = [
        r
        for r in reglementations
        if r["status"].status == ReglementationStatus.STATUS_NON_SOUMIS
    ]
    reglementations_recommandees = [
        r
        for r in reglementations
        if r["status"].status == ReglementationStatus.STATUS_RECOMMANDE
    ]

    return {
        "reglementations_a_actualiser": reglementations_a_actualiser,
        "reglementations_en_cours": reglementations_en_cours,
        "reglementations_a_jour": reglementations_a_jour,
        "autres_reglementations": reglementations_soumises
        + reglementations_recommandees
        + reglementations_non_soumises,
    }
