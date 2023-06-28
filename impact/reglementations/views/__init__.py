from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from entreprises.views import get_current_entreprise
from habilitations.models import is_user_attached_to_entreprise
from public.forms import CaracteristiquesForm
from public.forms import EntrepriseForm
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.dispositif_alerte import DispositifAlerteReglementation
from reglementations.views.index_egapro import IndexEgaproReglementation


def reglementations(request):
    entreprise = None
    caracteristiques = None
    if request.GET:
        entreprise_form = EntrepriseForm(request.GET)
        caracteristiques_form = CaracteristiquesForm(request.GET)
        if "siren" in request.GET:
            if entreprises := Entreprise.objects.filter(
                siren=entreprise_form.data["siren"]
            ):
                entreprise = entreprises[0]
                entreprise_form = EntrepriseForm(request.GET, instance=entreprise)
                commit = (
                    request.user.is_authenticated
                    and request.user in entreprise.users.all()
                )
            else:
                commit = True

            if entreprise_form.is_valid() and caracteristiques_form.is_valid():
                request.session["siren"] = entreprise_form.cleaned_data["siren"]
                entreprise = entreprise_form.save(commit=commit)
                if request.user.is_authenticated and is_user_attached_to_entreprise(
                    request.user, entreprise
                ):
                    request.session["entreprise"] = entreprise.siren
                last_year = date.today().year - 1
                try:
                    caracteristiques = CaracteristiquesAnnuelles.objects.get(
                        entreprise=entreprise, annee=last_year
                    )
                    caracteristiques_form = CaracteristiquesForm(
                        request.GET, instance=caracteristiques
                    )
                except ObjectDoesNotExist:
                    caracteristiques_form.instance.entreprise = entreprise
                    caracteristiques_form.instance.annee = last_year
                caracteristiques = caracteristiques_form.save(commit=commit)

    elif entreprise := get_current_entreprise(request):
        return redirect("reglementations:reglementations", siren=entreprise.siren)

    return render(
        request,
        "reglementations/reglementations.html",
        _reglementations_context(entreprise, caracteristiques, request.user),
    )


@login_required
def reglementations_for_entreprise(request, siren):
    entreprise = get_object_or_404(Entreprise, siren=siren)
    if not is_user_attached_to_entreprise(request.user, entreprise):
        raise PermissionDenied

    request.session["entreprise"] = entreprise.siren

    if not entreprise.est_qualifiee:
        messages.warning(
            request,
            "Veuillez renseigner les informations suivantes pour connaître les réglementations auxquelles est soumise cette entreprise",
        )
        return redirect("entreprises:qualification", siren=entreprise.siren)

    return render(
        request,
        "reglementations/reglementations.html",
        _reglementations_context(
            entreprise, entreprise.caracteristiques_actuelles(), request.user
        ),
    )


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
    ]
    return {
        "entreprise": entreprise,
        "reglementations": reglementations,
    }
