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
        return render(
            request,
            "reglementations/tableau_de_bord.html",
            context={
                "entreprise": entreprise,
                "reglementations": trie_reglementations_par_status(
                    caracteristiques, request.user
                ),
            },
        )
    else:
        messages.warning(
            request,
            "Veuillez renseigner les informations suivantes pour accéder au tableau de bord de cette entreprise.",
        )
        return redirect("entreprises:qualification", siren=entreprise.siren)


def trie_reglementations_par_status(
    caracteristiques: CaracteristiquesAnnuelles, user: settings.AUTH_USER_MODEL
):
    tri = {status.label: [] for status in ReglementationStatus.status_possibles()}
    for reglementation_et_status in calcule_reglementations(caracteristiques, user):
        tri[reglementation_et_status["status"].label].append(reglementation_et_status)
    return tri


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
