import requests
from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import redirect
from django.shortcuts import render

import api.exceptions
import api.recherche_entreprises
from .forms import ContactForm
from .forms import EligibiliteForm
from .forms import SirenForm
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
            reply_to = form.cleaned_data["email"]
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]
            full_message = f"Ce message a été envoyé par {reply_to} depuis {request.build_absolute_uri()} :\n\n{message}"
            email = EmailMessage(
                subject,
                full_message,
                to=[settings.CONTACT_EMAIL],
                reply_to=[reply_to],
            )
            if email.send():
                success_message = "Votre message a bien été envoyé"
                messages.success(request, success_message)
                return redirect("contact")
            else:
                error_message = "L'envoi du message a échoué"
                messages.error(request, error_message)
    else:
        if request.user.is_authenticated:
            initial = {"email": request.user.email}
        else:
            initial = None
        form = ContactForm(initial=initial)

    return render(request, "public/contact.html", {"form": form})


def siren(request):
    form = SirenForm(request.GET)
    if form.is_valid():
        siren = form.cleaned_data["siren"]
        try:
            infos_entreprise = api.recherche_entreprises.recherche(siren)
            form = EligibiliteForm(initial=infos_entreprise)
            return render(
                request,
                "public/siren.html",
                {
                    "raison_sociale": infos_entreprise["raison_sociale"],
                    "siren": siren,
                    "form": form,
                },
            )
        except api.exceptions.APIError:
            form.add_error("siren", "SIREN introuvable")
            messages.error(
                request,
                "L'entreprise n'a pas été trouvée. Vérifiez que le SIREN est correct.",
            )
    return render(request, "public/entreprise.html", {"form": form})
