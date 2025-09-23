from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import render

from entreprises.decorators import entreprise_qualifiee_requise
from entreprises.models import CaracteristiquesAnnuelles
from habilitations.views import contributeurs_context
from reglementations.utils import VSMEReglementation
from reglementations.views.audit_energetique import AuditEnergetiqueReglementation
from reglementations.views.base import ReglementationStatus
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.bges import BGESReglementation
from reglementations.views.csrd import CSRDReglementation
from reglementations.views.csrd.csrd import rapport_csrd
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


@login_required
@entreprise_qualifiee_requise
def tableau_de_bord(request, entreprise_qualifiee):
    caracteristiques = entreprise_qualifiee.dernieres_caracteristiques_qualifiantes
    reglementations_applicables = [
        reglementation
        for reglementation in REGLEMENTATIONS
        if reglementation.est_soumis(caracteristiques)
    ]
    nombre_reglementations_applicables = len(reglementations_applicables)

    context = {
        "entreprise": entreprise_qualifiee,
        "nombre_reglementations_applicables": nombre_reglementations_applicables,
        "page_resume": True,
    }
    context |= contributeurs_context(request, entreprise_qualifiee)

    return render(
        request,
        "reglementations/tableau_de_bord/resume.html",
        context=context,
    )


@login_required
@entreprise_qualifiee_requise
def reglementations(request, entreprise_qualifiee):
    caracteristiques = entreprise_qualifiee.dernieres_caracteristiques_qualifiantes
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
    return render(
        request,
        "reglementations/tableau_de_bord/reglementations.html",
        context={
            "entreprise": entreprise_qualifiee,
            "reglementations_a_actualiser": reglementations_a_actualiser,
            "reglementations_en_cours": reglementations_en_cours,
            "reglementations_a_jour": reglementations_a_jour,
            "autres_reglementations": reglementations_soumises
            + reglementations_recommandees
            + reglementations_non_soumises,
        },
    )


def calcule_reglementations(caracteristiques: CaracteristiquesAnnuelles):
    reglementations = [
        {
            "reglementation": reglementation,
            "status": reglementation.calculate_status(caracteristiques),
        }
        for reglementation in REGLEMENTATIONS
    ]
    return reglementations


@login_required
@entreprise_qualifiee_requise
def reglementation(request, entreprise_qualifiee, id_reglementation):
    reglementation = None
    for r in REGLEMENTATIONS:
        if r.id == id_reglementation:
            reglementation = r
            break
    if not reglementation:
        raise Http404

    caracteristiques = entreprise_qualifiee.dernieres_caracteristiques_qualifiantes
    status = reglementation.calculate_status(caracteristiques)

    template_name = f"reglementations/tableau_de_bord/{id_reglementation}.html"
    context = {
        "entreprise": entreprise_qualifiee,
        "reglementation": reglementation,
        "status": status,
    }
    if id_reglementation == "csrd":
        try:
            rapport = rapport_csrd(
                entreprise=entreprise_qualifiee,
                annee=datetime.today().year,
            )
        except ObjectDoesNotExist:
            rapport = None
        context["csrd"] = rapport

    return render(
        request,
        template_name,
        context=context,
    )
