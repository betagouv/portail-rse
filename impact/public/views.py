import time

import requests
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render, redirect

from .forms import EligibiliteForm, SirenForm, ContactForm
from entreprises.models import Entreprise


def index(request):
    return render(request, "public/index.html")


def entreprise(request):
    return render(request, "public/entreprise.html", {"form": SirenForm()})


def mentions_legales(request):
    return render(request, "public/mentions-legales.html")


def politique_confidentialite(request):
    return render(request, "public/politique-confidentialite.html")


def cgu(request):
    return render(request, "public/cgu.html")


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            from_email = form.cleaned_data["from_email"]
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]
            if send_mail(subject, message, from_email, [settings.CONTACT_EMAIL]):
                success_message = "Votre message a bien été envoyé"
                messages.success(request, success_message)
                return redirect("contact")
            else:
                error_message = "L'envoi du message a échoué"
                messages.error(request, error_message)
    else:
        if request.user.is_authenticated:
            initial = {"from_email": request.user.email}
        else:
            initial = None
        form = ContactForm(initial=initial)

    return render(request, "public/contact.html", {"form": form})


def siren(request):
    form = SirenForm(request.GET)
    if form.is_valid():
        siren = form.cleaned_data["siren"]
        # documentation api recherche d'entreprises 1.0.0 https://api.gouv.fr/documentation/api-recherche-entreprises
        url = f"https://recherche-entreprises.api.gouv.fr/search?q={siren}&page=1&per_page=1"
        response = requests.get(url)
        if response.status_code == 200 and response.json()["total_results"]:
            data = response.json()["results"][0]
            raison_sociale = data["nom_raison_sociale"]
            try:
                # les tranches d'effectif correspondent à celles de l'API Sirene de l'Insee
                # https://www.sirene.fr/sirene/public/variable/tefen
                tranche_effectif = int(data["tranche_effectif_salarie"])
            except (ValueError, TypeError):
                tranche_effectif = 0
            if tranche_effectif < 21:  # moins de 50 salariés
                taille = "petit"
            elif tranche_effectif < 32:  # moins de 250 salariés
                taille = "moyen"
            elif tranche_effectif < 41:  # moins de 500 salariés
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
                    "siren": siren,
                    "form": form,
                },
            )
        else:
            messages.error(
                request,
                "L'entreprise n'a pas été trouvée. Vérifiez que le SIREN est correct.",
            )
    return render(request, "public/index.html", {"form": form})
