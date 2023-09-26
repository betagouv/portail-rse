from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse_lazy

from entreprises.models import Entreprise
from entreprises.views import get_current_entreprise
from habilitations.models import is_user_attached_to_entreprise
from reglementations.views.audit_energetique import AuditEnergetiqueReglementation
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.bges import BGESReglementation
from reglementations.views.dispositif_alerte import DispositifAlerteReglementation
from reglementations.views.dispositif_anticorruption import DispositifAntiCorruption
from reglementations.views.index_egapro import IndexEgaproReglementation


REGLEMENTATIONS = [
    BDESEReglementation,
    IndexEgaproReglementation,
    DispositifAlerteReglementation,
    BGESReglementation,
    AuditEnergetiqueReglementation,
    DispositifAntiCorruption,
]


def reglementations(request):
    if entreprise := get_current_entreprise(request):
        return redirect("reglementations:reglementations", siren=entreprise.siren)

    context = {
        "reglementations": [
            {
                "info": reglementation.info(),
                "status": None,
            }
            for reglementation in REGLEMENTATIONS
        ],
        "simulation": False,
    }

    return render(
        request,
        "reglementations/reglementations.html",
        context,
    )


@login_required
def reglementations_for_entreprise(request, siren):
    entreprise = get_object_or_404(Entreprise, siren=siren)
    if not is_user_attached_to_entreprise(request.user, entreprise):
        raise PermissionDenied

    request.session["entreprise"] = entreprise.siren

    if caracteristiques := entreprise.dernieres_caracteristiques_qualifiantes:
        if caracteristiques != entreprise.caracteristiques_actuelles():
            messages.warning(
                request,
                f"Les réglementations sont basées sur des informations de l'exercice {caracteristiques.annee}. <a href='{reverse_lazy('entreprises:qualification', args=[entreprise.siren])}'>Mettre à jour les informations de l'entreprise.</a>",
            )
        return render(
            request,
            "reglementations/reglementations.html",
            context={
                "entreprise": entreprise,
                "reglementations": calcule_reglementations(
                    entreprise, caracteristiques, request.user
                ),
                "simulation": False,
            },
        )
    else:
        messages.warning(
            request,
            "Veuillez renseigner les informations suivantes pour connaître les réglementations auxquelles est soumise cette entreprise",
        )
        return redirect("entreprises:qualification", siren=entreprise.siren)


def calcule_reglementations(entreprise, caracteristiques, user):
    return [
        {
            "info": reglementation.info(),
            "status": reglementation.calculate_status(caracteristiques, user)
            if entreprise
            else None,
        }
        for reglementation in REGLEMENTATIONS
    ]
