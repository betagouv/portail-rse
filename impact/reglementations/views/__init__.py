from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse_lazy

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from entreprises.views import get_current_entreprise
from habilitations.models import Habilitation
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


def entreprise_qualifiee_requise(function):
    @wraps(function)
    def wrap(request, siren=None, **kwargs):
        if not siren:
            entreprise = get_current_entreprise(request)
            if not entreprise:
                messages.warning(
                    request,
                    "Commencez par ajouter une entreprise à votre compte utilisateur avant d'accéder à votre tableau de bord",
                )
                return redirect("entreprises:entreprises")
            return redirect("reglementations:tableau_de_bord", siren=entreprise.siren)

        entreprise = get_object_or_404(Entreprise, siren=siren)
        if not Habilitation.existe(entreprise, request.user):
            raise PermissionDenied

        request.session["entreprise"] = entreprise.siren

        if caracteristiques := entreprise.dernieres_caracteristiques_qualifiantes:
            if caracteristiques != entreprise.caracteristiques_actuelles():
                messages.warning(
                    request,
                    f"Les informations affichées sont basées sur l'exercice comptable {caracteristiques.annee}. <a href='{reverse_lazy('entreprises:qualification', args=[entreprise.siren])}'>Mettre à jour le profil de l'entreprise.</a>",
                )
            return function(request, entreprise, **kwargs)

        else:
            messages.warning(
                request,
                "Veuillez renseigner les informations suivantes pour accéder au tableau de bord de cette entreprise.",
            )
            return redirect("entreprises:qualification", siren=entreprise.siren)

    return wrap


@login_required
@entreprise_qualifiee_requise
def tableau_de_bord(request, entreprise_qualifiee):
    return render(
        request,
        "reglementations/tableau_de_bord/resume.html",
        context={
            "entreprise": entreprise_qualifiee,
        },
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

    return render(
        request,
        template_name,
        context=context,
    )
