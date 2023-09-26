from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

from .forms import ContactForm
from reglementations.forms import SimulationForm


def index(request):
    if request.user.is_authenticated:
        return redirect(reverse("reglementations:reglementations"))
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
    return render(
        request,
        "public/simulation.html",
        {
            "svelte_form_data": {"csrfToken": get_token(request)},
            "simulation_form": SimulationForm(),
        },
    )
