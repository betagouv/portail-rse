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

REGLEMENTATIONS = [
    BDESEReglementation,
    IndexEgaproReglementation,
    DispositifAlerteReglementation,
    BGESReglementation,
    AuditEnergetiqueReglementation,
]


def reglementations(request):
    entreprise = None
    caracteristiques = None
    simulation = True
    if request.POST:
        simulation_form = SimulationForm(request.POST)
        if simulation_form.is_valid():
            if entreprises := Entreprise.objects.filter(
                siren=simulation_form.data["siren"]
            ):
                entreprise = entreprises[0]
                entreprise.denomination = simulation_form.cleaned_data["denomination"]
            else:
                entreprise = Entreprise.objects.create(
                    denomination=simulation_form.cleaned_data["denomination"],
                    siren=simulation_form.data["siren"],
                )

            request.session["siren"] = simulation_form.cleaned_data["siren"]
            if request.user.is_authenticated and is_user_attached_to_entreprise(
                request.user, entreprise
            ):
                request.session["entreprise"] = entreprise.siren

            date_cloture_exercice = date(date.today().year - 1, 12, 31)
            actualisation = ActualisationCaracteristiquesAnnuelles(
                date_cloture_exercice=date_cloture_exercice,
                effectif=simulation_form.data["effectif"],
                effectif_outre_mer=None,
                tranche_chiffre_affaires=simulation_form.data[
                    "tranche_chiffre_affaires"
                ],
                tranche_bilan=simulation_form.data["tranche_bilan"],
                tranche_chiffre_affaires_consolide=None,
                tranche_bilan_consolide=None,
                bdese_accord=False,  # None serait préférable si bdese_accord est nullable
                systeme_management_energie=None,
            )
            caracteristiques = entreprise.actualise_caracteristiques(actualisation)
            if should_commit(entreprise):
                caracteristiques.save()

            entreprise, caracteristiques = enrichit_les_donnees_pour_la_simulation(
                entreprise, caracteristiques
            )

        else:
            return redirect("simulation")

    elif entreprise := get_current_entreprise(request):
        return redirect("reglementations:reglementations", siren=entreprise.siren)
    else:  # affichage simple des réglementations
        simulation = False

    return render(
        request,
        "reglementations/reglementations.html",
        _reglementations_context(
            entreprise, caracteristiques, request.user, simulation=simulation
        ),
    )


def enrichit_les_donnees_pour_la_simulation(entreprise, caracteristiques):
    entreprise.appartient_groupe = False
    entreprise.comptes_consolides = False
    caracteristiques.effectif_outre_mer = (
        CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250
    )
    caracteristiques.bdese_accord = False
    caracteristiques.systeme_management_energie = False
    return (entreprise, caracteristiques)


def should_commit(entreprise):
    return not entreprise.users.all() and not entreprise.caracteristiques_actuelles()


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
            _reglementations_context(
                entreprise, caracteristiques, request.user, simulation=False
            ),
        )
    else:
        messages.warning(
            request,
            "Veuillez renseigner les informations suivantes pour connaître les réglementations auxquelles est soumise cette entreprise",
        )
        return redirect("entreprises:qualification", siren=entreprise.siren)


def _reglementations_context(entreprise, caracteristiques, user, simulation):
    reglementations = [
        {
            "info": reglementation.info(),
            "status": reglementation(entreprise).calculate_status(
                caracteristiques, user
            )
            if entreprise
            else None,
        }
        for reglementation in REGLEMENTATIONS
    ]
    return {
        "entreprise": entreprise,
        "reglementations": reglementations,
        "simulation": simulation,
    }
