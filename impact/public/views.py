from datetime import date

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from entreprises.views import ActualisationCaracteristiquesAnnuelles
from habilitations.models import is_user_attached_to_entreprise
from public.forms import ContactForm
from public.forms import SimulationForm
from reglementations.views import calcule_reglementations


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
    if request.POST:
        return calcule_simulation(request)
    return render(
        request,
        "public/simulation.html",
        {
            "simulation_form": SimulationForm(),
        },
    )


def calcule_simulation(request):
    entreprise = None
    caracteristiques = None
    simulation_form = SimulationForm(request.POST)
    if simulation_form.is_valid():
        if entreprises := Entreprise.objects.filter(
            siren=simulation_form.cleaned_data["siren"]
        ):
            entreprise = entreprises[0]
            entreprise.denomination = simulation_form.cleaned_data["denomination"]
            entreprise.appartient_groupe = simulation_form.cleaned_data[
                "appartient_groupe"
            ]
            entreprise.comptes_consolides = simulation_form.cleaned_data[
                "comptes_consolides"
            ]
        else:
            entreprise = Entreprise.objects.create(
                denomination=simulation_form.cleaned_data["denomination"],
                siren=simulation_form.cleaned_data["siren"],
                appartient_groupe=simulation_form.cleaned_data["appartient_groupe"],
                comptes_consolides=simulation_form.cleaned_data["comptes_consolides"],
            )
        request.session["siren"] = simulation_form.cleaned_data["siren"]
        if request.user.is_authenticated and is_user_attached_to_entreprise(
            request.user, entreprise
        ):
            request.session["entreprise"] = entreprise.siren
        date_cloture_exercice = date(date.today().year - 1, 12, 31)
        actualisation = ActualisationCaracteristiquesAnnuelles(
            date_cloture_exercice=date_cloture_exercice,
            effectif=simulation_form.cleaned_data["effectif"],
            effectif_outre_mer=None,
            effectif_groupe=simulation_form.cleaned_data["effectif_groupe"],
            tranche_chiffre_affaires=simulation_form.cleaned_data[
                "tranche_chiffre_affaires"
            ],
            tranche_bilan=simulation_form.cleaned_data["tranche_bilan"],
            tranche_chiffre_affaires_consolide=simulation_form.cleaned_data[
                "tranche_chiffre_affaires_consolide"
            ],
            tranche_bilan_consolide=simulation_form.cleaned_data[
                "tranche_bilan_consolide"
            ],
            bdese_accord=None,
            systeme_management_energie=None,
        )
        caracteristiques = entreprise.actualise_caracteristiques(actualisation)
        if should_commit(entreprise):
            entreprise.save()
            caracteristiques.save()
        caracteristiques = enrichit_les_donnees_pour_la_simulation(caracteristiques)
    else:
        messages.error(
            request,
            f"Impossible de finaliser la simulation car le formulaire contient des erreurs.",
        )
    context = {
        "entreprise": entreprise,
        "reglementations": calcule_reglementations(
            entreprise, caracteristiques, request.user
        ),
        "simulation": True,
        "simulation_form": simulation_form,
    }
    return render(
        request,
        "public/simulation.html",
        context,
    )


def enrichit_les_donnees_pour_la_simulation(caracteristiques):
    caracteristiques.entreprise.societe_mere_en_france = True
    caracteristiques.effectif_outre_mer = (
        CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250
    )
    caracteristiques.bdese_accord = False
    caracteristiques.systeme_management_energie = False
    return caracteristiques


def should_commit(entreprise):
    return not entreprise.users.all() and not entreprise.caracteristiques_actuelles()
