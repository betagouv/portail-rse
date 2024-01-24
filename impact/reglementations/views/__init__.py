from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse_lazy

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from habilitations.models import is_user_attached_to_entreprise
from reglementations.views.audit_energetique import AuditEnergetiqueReglementation
from reglementations.views.base import ReglementationStatus
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.bges import BGESReglementation
from reglementations.views.csrd import csrd  # noqa
from reglementations.views.dispositif_alerte import DispositifAlerteReglementation
from reglementations.views.dispositif_anticorruption import DispositifAntiCorruption
from reglementations.views.dpef import DPEFReglementation
from reglementations.views.index_egapro import IndexEgaproReglementation
from reglementations.views.plan_vigilance import PlanVigilanceReglementation

REGLEMENTATIONS = [
    BDESEReglementation,
    IndexEgaproReglementation,
    DispositifAlerteReglementation,
    BGESReglementation,
    AuditEnergetiqueReglementation,
    DispositifAntiCorruption,
    DPEFReglementation,
    PlanVigilanceReglementation,
]


@login_required
def tableau_de_bord(request, siren):
    entreprise = get_object_or_404(Entreprise, siren=siren)
    if not is_user_attached_to_entreprise(request.user, entreprise):
        raise PermissionDenied

    request.session["entreprise"] = entreprise.siren

    if caracteristiques := entreprise.dernieres_caracteristiques_qualifiantes:
        if caracteristiques != entreprise.caracteristiques_actuelles():
            messages.warning(
                request,
                f"Les réglementations affichées sont basées sur des informations de l'exercice comptable {caracteristiques.annee}. <a href='{reverse_lazy('entreprises:qualification', args=[entreprise.siren])}'>Mettre à jour les informations de l'entreprise.</a>",
            )
        reglementations = calcule_reglementations(caracteristiques, request.user)
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
        return render(
            request,
            "reglementations/tableau_de_bord.html",
            context={
                "entreprise": entreprise,
                "reglementations_a_actualiser": reglementations_a_actualiser,
                "reglementations_en_cours": reglementations_en_cours,
                "reglementations_a_jour": reglementations_a_jour,
                "reglementations_soumises": reglementations_soumises,
                "reglementations_non_soumises": reglementations_non_soumises,
            },
        )
    else:
        messages.warning(
            request,
            "Veuillez renseigner les informations suivantes pour accéder au tableau de bord de cette entreprise.",
        )
        return redirect("entreprises:qualification", siren=entreprise.siren)


def calcule_reglementations(
    caracteristiques: CaracteristiquesAnnuelles, user: settings.AUTH_USER_MODEL
):
    reglementations = [
        {
            "reglementation": reglementation,
            "status": reglementation.calculate_status(caracteristiques, user),
        }
        for reglementation in REGLEMENTATIONS
    ]
    return sorted(reglementations, key=lambda x: x["status"].status)
