import requests
from django.conf import settings
from django.shortcuts import render

from .forms import EligibiliteForm, SirenForm
from entreprises.models import Entreprise


def index(request):
    return render(request, "public/index.html", {"form": SirenForm()})


def siren(request):
    form = SirenForm(request.GET)
    errors = []
    if form.is_valid():
        siren = form.cleaned_data["siren"]

        url = f"https://entreprise.api.gouv.fr/v3/insee/sirene/unites_legales/{siren}"
        headers = {"Authorization": f"Bearer {settings.API_ENTREPRISE_TOKEN}"}
        params = {
            "context": "Test de l'API",
            "object": "Test de l'API",
            "recipient": "10000001700010",
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()["data"]
            raison_sociale = data["personne_morale_attributs"]["raison_sociale"]
            effectif = data["tranche_effectif_salarie"]["a"]
            if effectif < 50:
                taille = "petit"
            elif effectif < 300:
                taille = "moyen"
            elif effectif < 500:
                taille = "grand"
            else:
                taille = "sup500"
            form = EligibiliteForm(
                initial={
                    "siren": siren,
                    "effectif": taille,
                    "raison_sociale": raison_sociale,
                }
            )
            return render(
                request,
                "public/siren.html",
                {
                    "raison_sociale": raison_sociale,
                    "form": form,
                },
            )
        else:
            errors = response.json()["errors"]
    else:
        errors = form.errors

    return render(request, "public/index.html", {"form": form, "errors": errors})
