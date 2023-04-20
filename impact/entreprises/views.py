from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

import api.recherche_entreprises
from .forms import EntrepriseAttachForm
from .forms import EntrepriseDetachForm
from .forms import EntrepriseQualificationForm
from .models import Entreprise
from api.exceptions import APIError
from habilitations.models import attach_user_to_entreprise
from habilitations.models import detach_user_from_entreprise
from habilitations.models import get_habilitation
from habilitations.models import is_user_attached_to_entreprise


@login_required()
def index(request):
    if request.POST:
        if request.POST["action"] == "attach":
            return attach(request)
        else:
            form = EntrepriseDetachForm(request.POST)
            if form.is_valid():
                siren = form.cleaned_data["siren"]
                try:
                    entreprise = Entreprise.objects.get(siren=siren)
                    detach_user_from_entreprise(request.user, entreprise)
                    entreprise_in_session = request.session.get("entreprise")
                    if entreprise_in_session == entreprise.siren:
                        del request.session["entreprise"]
                    messages.success(
                        request, "Vous n'êtes plus rattaché à cette entreprise"
                    )
                except ObjectDoesNotExist:
                    messages.error(
                        request, "Impossible de se retirer de cette entreprise"
                    )
            return redirect("entreprises:entreprises")

    return render(request, "entreprises/index.html", {"form": EntrepriseAttachForm()})


class _InvalidRequest(Exception):
    pass


def search_and_create_entreprise(siren):
    try:
        infos_entreprise = api.recherche_entreprises.recherche(siren)
    except APIError as exception:
        raise exception
    return Entreprise.objects.create(
        siren=infos_entreprise["siren"],
        denomination=infos_entreprise["denomination"],
    )


def attach(request):
    form = EntrepriseAttachForm(request.POST)
    try:
        if form.is_valid():
            siren = form.cleaned_data["siren"]
            if entreprises := Entreprise.objects.filter(siren=siren):
                entreprise = entreprises[0]
            else:
                entreprise = search_and_create_entreprise(siren)
            if is_user_attached_to_entreprise(request.user, entreprise):
                raise _InvalidRequest(
                    "Impossible d'ajouter cette entreprise. Vous y êtes déjà rattaché·e."
                )
            else:
                attach_user_to_entreprise(
                    request.user,
                    entreprise,
                    form.cleaned_data["fonctions"],
                )
        else:
            raise _InvalidRequest(
                "Impossible de créer l'entreprise car les données sont incorrectes."
            )
    except (_InvalidRequest, APIError) as exception:
        messages.error(
            request,
            exception,
        )
        return render(request, "entreprises/index.html", {"form": form})

    messages.success(request, "L'entreprise a été ajoutée.")
    return redirect("entreprises:entreprises")


@login_required
def qualification(request, siren):
    entreprise = get_object_or_404(Entreprise, siren=siren)
    if request.user not in entreprise.users.all():
        raise PermissionDenied

    if request.POST:
        form = EntrepriseQualificationForm(data=request.POST, instance=entreprise)
        if form.is_valid():
            entreprise = form.save()
            messages.success(request, "Entreprise enregistrée")
            return redirect("reglementations:reglementation", siren=siren)
        else:
            messages.error(
                request,
                "L'entreprise n'a pas été enregistrée car le formulaire contient des erreurs",
            )

    else:
        infos_entreprise = api.recherche_entreprises.recherche(entreprise.siren)
        if not entreprise.denomination:
            # Certaines entreprises peuvent avoir été créées sans raison sociale depuis le formulaire de création utilisateur
            # TODO: supprimer ce bloc conditionnel quand toutes les entreprises auront une raison sociale et qu'une entreprise ne pourra pas être créée sans
            entreprise.denomination = infos_entreprise["denomination"]
            entreprise.save()
        form = EntrepriseQualificationForm(
            instance=entreprise, initial=infos_entreprise
        )

    return render(
        request,
        "entreprises/qualification.html",
        context={"entreprise": entreprise, "form": form},
    )


def search_entreprise(request, siren):
    try:
        return JsonResponse(api.recherche_entreprises.recherche(siren))
    except APIError as exception:
        return JsonResponse(
            {"error": str(exception)},
            status=400,
        )
