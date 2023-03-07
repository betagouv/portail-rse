import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect, render

from .forms import EntrepriseCreationForm
from .models import Entreprise
from api.exceptions import APIError
from habilitations.models import Habilitation

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
                entreprise = Entreprise.objects.create(**infos_entreprise)
            if habilitations := Habilitation.objects.filter(
                user=request.user, entreprise=entreprise
            ):
                raise _InvalidRequest(
                    "Impossible d'ajouter cette entreprise. Vous y êtes déjà rattaché·e."
                )
            else:
                Habilitation.objects.create(
                    user=request.user,
                    entreprise=entreprise,
                    fonctions=form.cleaned_data["fonctions"],
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


def search_entreprise(request, siren):
    try:
        return JsonResponse(api.recherche_entreprises.recherche(siren))
    except APIError:
        return JsonResponse(
            {"error": SIREN_NOT_FOUND_ERROR},
            status=400,
        )
