import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EntrepriseCreationForm, EntrepriseQualificationForm
from .models import Entreprise
from api.exceptions import APIError
from habilitations.models import add_entreprise_to_user, get_habilitation

import api.recherche_entreprises


@login_required()
def index(request):
    csrf_token = get_token(request)
    return render(request, "entreprises/index.html", {"csrf_token": csrf_token})


class _InvalidRequest(Exception):
    pass


SIREN_NOT_FOUND_ERROR = (
    "Impossible de créer l'entreprise car le SIREN n'est pas trouvé."
)


@login_required()
def add(request):
    form = EntrepriseCreationForm(request.POST)
    try:
        if form.is_valid():
            siren = form.cleaned_data["siren"]
            if entreprises := Entreprise.objects.filter(siren=siren):
                entreprise = entreprises[0]
            else:
                try:
                    infos_entreprise = api.recherche_entreprises.recherche(siren)
                except APIError:
                    raise _InvalidRequest(SIREN_NOT_FOUND_ERROR)
                entreprise = Entreprise.objects.create(
                    siren=infos_entreprise["siren"],
                    raison_sociale=infos_entreprise["raison_sociale"],
                )
            if get_habilitation(entreprise, request.user):
                raise _InvalidRequest(
                    "Impossible d'ajouter cette entreprise. Vous y êtes déjà rattaché·e."
                )
            else:
                add_entreprise_to_user(
                    entreprise,
                    request.user,
                    form.cleaned_data["fonctions"],
                )
        else:
            raise _InvalidRequest(
                "Impossible de créer l'entreprise car les données sont incorrectes."
            )
    except _InvalidRequest as exception:
        messages.error(
            request,
            exception,
        )
        return render(request, "entreprises/index.html", {"form": form})

    messages.success(request, "L'entreprise a été ajoutée.")
    return redirect("entreprises")


def detail_entreprise(request, siren):
    entreprise = get_object_or_404(Entreprise, siren=siren)

    if request.POST:
        form = EntrepriseQualificationForm(data=request.POST, instance=entreprise)
        if form.is_valid():
            entreprise = form.save()
            messages.success(request, "Entreprise enregistrée")
            return redirect("reglementation", siren=siren)
        else:
            messages.error(
                request,
                "L'entreprise n'a pas été enregistrée car le formulaire contient des erreurs",
            )
    else:
        infos_entreprise = api.recherche_entreprises.recherche(entreprise.siren)
        if not entreprise.raison_sociale:
            # some entreprises may have been created without raison sociale through user creation page
            entreprise.raison_sociale = infos_entreprise["raison_sociale"]
            entreprise.save()
        form = EntrepriseQualificationForm(
            instance=entreprise, initial=infos_entreprise
        )

    return render(
        request,
        "entreprises/detail_entreprise.html",
        context={"entreprise": entreprise, "form": form},
    )


def search_entreprise(request, siren):
    try:
        return JsonResponse(api.recherche_entreprises.recherche(siren))
    except APIError:
        return JsonResponse(
            {"error": SIREN_NOT_FOUND_ERROR},
            status=400,
        )
