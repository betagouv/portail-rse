from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import redirect
from django.shortcuts import render

import api.exceptions
import api.recherche_entreprises
from .forms import CaracteristiquesForm
from .forms import ContactForm
from .forms import EntrepriseForm
from .forms import SirenForm
from entreprises.models import CaracteristiquesAnnuelles


def index(request):
    return render(request, "public/index.html")


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
            error_message = "L'envoi du message a échoué"
            messages.error(request, error_message)

    else:
        if request.user.is_authenticated:
            initial = {"email": request.user.email}
        else:
            initial = None
        form = ContactForm(initial=initial)

    return render(request, "public/contact.html", {"form": form})


def simulation(request):
    siren_form = SirenForm(request.GET or None)
    if request.GET:
        if siren_form.is_valid():
            siren = siren_form.cleaned_data["siren"]
            try:
                infos_entreprise = api.recherche_entreprises.recherche(siren)
                infos_entreprise[
                    "effectif_outre_mer"
                ] = CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250
                entreprise_form = EntrepriseForm(initial=infos_entreprise)
                caracteristiques_form = CaracteristiquesForm(initial=infos_entreprise)
                return render(
                    request,
                    "public/simulation-etape-2.html",
                    {
                        "denomination": infos_entreprise["denomination"],
                        "siren": siren,
                        "entreprise_form": entreprise_form,
                        "caracteristiques_form": caracteristiques_form,
                    },
                )
            except api.exceptions.SirenError as e:
                siren_form.add_error("siren", "SIREN introuvable")
                messages.error(
                    request,
                    str(e),
                )
            except api.exceptions.APIError as e:
                messages.error(
                    request,
                    str(e),
                )
    return render(request, "public/simulation-etape-1.html", {"form": siren_form})
