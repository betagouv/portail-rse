from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from entreprises.models import ActualisationCaracteristiquesAnnuelles
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from entreprises.views import get_current_entreprise
from habilitations.models import is_user_attached_to_entreprise
from reglementations.forms import SimulationForm
from reglementations.views.audit_energetique import AuditEnergetiqueReglementation
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.bges import BGESReglementation
from reglementations.views.dispositif_alerte import DispositifAlerteReglementation
from reglementations.views.index_egapro import IndexEgaproReglementation


def reglementations(request):
    entreprise = None
    caracteristiques = None
    if request.POST:
        simulation_form = SimulationForm(request.POST)
        if "siren" in request.POST:
            if entreprises := Entreprise.objects.filter(
                siren=simulation_form.data["siren"]
            ):
                entreprise = entreprises[0]
                entreprise.denomination = simulation_form.cleaned_data["denomination"]
                commit = not entreprise.caracteristiques_actuelles()
            else:
                entreprise = Entreprise.objects.create(
                    denomination=simulation_form.cleaned_data["denomination"],
                    siren=simulation_form.data["siren"],
                    date_cloture_exercice=date(date.today().year - 1, 12, 31),
                    comptes_consolides=None,
                )
                commit = True
            if simulation_form.is_valid():
                request.session["siren"] = simulation_form.cleaned_data["siren"]
                if request.user.is_authenticated and is_user_attached_to_entreprise(
                    request.user, entreprise
                ):
                    request.session["entreprise"] = entreprise.siren
                date_cloture_exercice = date(date.today().year - 1, 12, 31)
                actualisation = ActualisationCaracteristiquesAnnuelles(
                    date_cloture_exercice=date_cloture_exercice,
                    effectif=simulation_form.data["effectif"],
                    effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
                    tranche_chiffre_affaires=simulation_form.data[
                        "tranche_chiffre_affaires"
                    ],
                    tranche_bilan=simulation_form.data["tranche_bilan"],
                    tranche_chiffre_affaires_consolide=None,
                    tranche_bilan_consolide=None,
                    bdese_accord=False,
                    systeme_management_energie=False,
                )
                caracteristiques = entreprise.actualise_caracteristiques(actualisation)
                if commit:
                    caracteristiques.save()

    elif entreprise := get_current_entreprise(request):
        return redirect("reglementations:reglementations", siren=entreprise.siren)

    return render(
        request,
        "reglementations/reglementations.html",
        _reglementations_context(entreprise, caracteristiques, request.user),
    )


def should_commit(entreprise, user):
    return (
        not entreprise
        or not entreprise.users.all()
        or is_user_attached_to_entreprise(user, entreprise)
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
                f"Les informations sont basées sur des données de l'exercice {caracteristiques.annee}.",
            )
        return render(
            request,
            "reglementations/reglementations.html",
            _reglementations_context(entreprise, caracteristiques, request.user),
        )
    else:
        messages.warning(
            request,
            "Veuillez renseigner les informations suivantes pour connaître les réglementations auxquelles est soumise cette entreprise",
        )
        return redirect("entreprises:qualification", siren=entreprise.siren)


def _reglementations_context(entreprise, caracteristiques, user):
    reglementations = [
        {
            "info": BDESEReglementation.info(),
            "status": BDESEReglementation(entreprise).calculate_status(
                caracteristiques, user
            )
            if entreprise
            else None,
        },
        {
            "info": IndexEgaproReglementation.info(),
            "status": IndexEgaproReglementation(entreprise).calculate_status(
                caracteristiques, user
            )
            if entreprise
            else None,
        },
        {
            "info": DispositifAlerteReglementation.info(),
            "status": DispositifAlerteReglementation(entreprise).calculate_status(
                caracteristiques, user
            )
            if entreprise
            else None,
        },
        {
            "info": BGESReglementation.info(),
            "status": BGESReglementation(entreprise).calculate_status(
                caracteristiques, user
            )
            if entreprise
            else None,
        },
        {
            "info": AuditEnergetiqueReglementation.info(),
            "status": AuditEnergetiqueReglementation(entreprise).calculate_status(
                caracteristiques, user
            )
            if entreprise
            else None,
        },
    ]
    return {
        "entreprise": entreprise,
        "reglementations": reglementations,
    }
