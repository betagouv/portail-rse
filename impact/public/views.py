from django.conf import settings
from django.shortcuts import render
import requests


def index(request):
    return render(request, "public/index.html")


def siren(request):
    siren = request.GET["siren"]

    url = f"https://entreprise.api.gouv.fr/v3/insee/sirene/unites_legales/{siren}"
    headers = {"Authorization": f"Bearer {settings.API_ENTREPRISE_TOKEN}"}
    params = {
        "context": "Test de l'API",
        "object": "Test de l'API",
        "recipient": "10000001700010"
    }
    response = requests.get(url, headers=headers, params=params)
    return render(request, "public/siren.html", {
        "siren": siren,
        "response": response.json(),
        })
