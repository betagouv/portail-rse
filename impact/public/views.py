from datetime import date

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import redirect
from django.shortcuts import render

import api.infos_entreprise
from api.exceptions import APIError
from entreprises.models import ActualisationCaracteristiquesAnnuelles
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from entreprises.models import SIREN_ENTREPRISE_TEST
from entreprises.views import get_current_entreprise
from public.forms import ContactForm
from public.forms import SimulationForm
from reglementations.views import REGLEMENTATIONS


def index(request):
    if request.user.is_authenticated:
        referer = request.META.get("HTTP_REFERER", "")
        if referer.endswith("/connexion") or referer.endswith("/connexion?next=/"):
            if entreprise := get_current_entreprise(request):
                return redirect(
                    "reglementations:tableau_de_bord", siren=entreprise.siren
                )
            else:
                return redirect("entreprises:entreprises")
    return render(request, "public/index.html")


def fragment_liens_menu(request):
    return render(
        request,
        "snippets/entete_page.html",
    )


def stats(request):
    return render(request, "public/stats.html")


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
    simulation_form = SimulationForm(request.POST or None)
    if request.POST:
        if simulation_form.is_valid():
            request.session["simulation"] = simulation_form.cleaned_data
            request.session["siren"] = simulation_form.cleaned_data["siren"]
            return redirect("resultats_simulation")
        else:
            messages.error(
                request,
                "Impossible de finaliser la simulation car le formulaire contient des erreurs.",
            )
    elif request.session.get("simulation"):
        form = SimulationForm(request.session["simulation"])
        if form.is_valid():
            simulation_form = form
    return render(
        request,
        "public/simulation.html",
        {
            "simulation_form": simulation_form,
        },
    )


def preremplissage_formulaire_simulation(request, siren):
    erreur = False
    if siren == SIREN_ENTREPRISE_TEST:
        infos = {
            "siren": SIREN_ENTREPRISE_TEST,
            "denomination": "ENTREPRISE TEST",
            "effectif": CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
            "categorie_juridique_sirene": 5505,
            "code_NAF": "01.11Z",
            "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
            "tranche_bilan": CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        }
    else:
        try:
            infos = api.infos_entreprise.infos_entreprise(
                siren, donnees_financieres=True
            )
            if infos.get("tranche_chiffre_affaires_consolide"):
                # L'entreprise appartient à un groupe et établit des comptes consolidés
                infos["appartient_groupe"] = True
                infos["comptes_consolides"] = True
        except APIError as e:
            # Ce cas est actuellement bloquant pour la suite de la simulation car certaines données sont récupérées par l'API
            # sans que l'utilisateur ne puisse voir/modifier cette donnée par soucis de simplicité (par ex la denomination).
            # Depuis l'ajout de la recherche d'entreprise par nom ou siren en première étape de la simulation,
            # cette donnée pourrait éventuellement être récupérée lors de l'appel API de recherche puis transmise à cette vue.
            # On pourrait alors simplifier cet appel API pour ne chercher que la donnée financière éventuelle
            # et le rendre non bloquant pour la simulation
            erreur = str(e)
            infos = {}
    simulation_form = SimulationForm(initial=infos)
    return render(
        request,
        "fragments/simulation_form.html",
        context={"simulation_form": simulation_form, "erreur": erreur},
    )


def resultats_simulation(request):
    if "simulation" not in request.session:
        return redirect("simulation")

    simulation_form = SimulationForm(request.session["simulation"])
    if simulation_form.is_valid():
        reglementations_applicables = calcule_simulation(simulation_form)
        siren = simulation_form.cleaned_data["siren"]
    else:
        return redirect("simulation")
    return render(
        request,
        "public/resultats_simulation.html",
        {
            "reglementations_applicables": reglementations_applicables,
            "siren": siren,
        },
    )


def calcule_simulation(simulation_form):
    if entreprises := Entreprise.objects.filter(
        siren=simulation_form.cleaned_data["siren"]
    ):
        entreprise = entreprises[0]
        entreprise.denomination = simulation_form.cleaned_data["denomination"]
        entreprise.categorie_juridique_sirene = simulation_form.cleaned_data[
            "categorie_juridique_sirene"
        ]
        entreprise.code_pays_etranger_sirene = simulation_form.cleaned_data[
            "code_pays_etranger_sirene"
        ]
        entreprise.code_NAF = simulation_form.cleaned_data["code_NAF"]
        entreprise.est_cotee = simulation_form.cleaned_data["est_cotee"]
        entreprise.appartient_groupe = simulation_form.cleaned_data["appartient_groupe"]
        entreprise.est_societe_mere = simulation_form.cleaned_data["est_societe_mere"]
        entreprise.comptes_consolides = simulation_form.cleaned_data[
            "comptes_consolides"
        ]
    else:
        entreprise = Entreprise.objects.create(
            denomination=simulation_form.cleaned_data["denomination"],
            siren=simulation_form.cleaned_data["siren"],
            categorie_juridique_sirene=simulation_form.cleaned_data[
                "categorie_juridique_sirene"
            ],
            code_pays_etranger_sirene=simulation_form.cleaned_data[
                "code_pays_etranger_sirene"
            ],
            code_NAF=simulation_form.cleaned_data["code_NAF"],
            est_cotee=simulation_form.cleaned_data["est_cotee"],
            appartient_groupe=simulation_form.cleaned_data["appartient_groupe"],
            est_societe_mere=simulation_form.cleaned_data["est_societe_mere"],
            comptes_consolides=simulation_form.cleaned_data["comptes_consolides"],
        )

    date_cloture_exercice = date(date.today().year - 1, 12, 31)
    actualisation = ActualisationCaracteristiquesAnnuelles(
        date_cloture_exercice=date_cloture_exercice,
        effectif=simulation_form.cleaned_data["effectif"],
        effectif_securite_sociale=None,
        effectif_permanent=None,
        effectif_outre_mer=None,
        effectif_groupe=simulation_form.cleaned_data["effectif_groupe"],
        effectif_groupe_france=None,
        effectif_groupe_permanent=None,
        tranche_chiffre_affaires=simulation_form.cleaned_data[
            "tranche_chiffre_affaires"
        ],
        tranche_bilan=simulation_form.cleaned_data["tranche_bilan"],
        tranche_chiffre_affaires_consolide=simulation_form.cleaned_data[
            "tranche_chiffre_affaires_consolide"
        ],
        tranche_bilan_consolide=simulation_form.cleaned_data["tranche_bilan_consolide"],
        bdese_accord=None,
        systeme_management_energie=None,
    )
    caracteristiques = entreprise.actualise_caracteristiques(actualisation)
    if should_commit(entreprise):
        entreprise.save()
        caracteristiques.save()
    caracteristiques = enrichit_les_donnees_pour_la_simulation(caracteristiques)
    return [
        reglementation
        for reglementation in REGLEMENTATIONS
        if reglementation.est_soumis(caracteristiques)
    ]


def enrichit_les_donnees_pour_la_simulation(caracteristiques):
    caracteristiques.entreprise.est_interet_public = False
    caracteristiques.entreprise.societe_mere_en_france = True
    caracteristiques.effectif_securite_sociale = caracteristiques.effectif
    caracteristiques.effectif_permanent = caracteristiques.effectif
    caracteristiques.effectif_outre_mer = (
        CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250
    )
    if caracteristiques.entreprise.appartient_groupe:
        caracteristiques.effectif_groupe_france = caracteristiques.effectif_groupe
        caracteristiques.effectif_groupe_permanent = caracteristiques.effectif_groupe
    caracteristiques.bdese_accord = False
    caracteristiques.systeme_management_energie = False
    return caracteristiques


def should_commit(entreprise):
    return not entreprise.users.all() and not entreprise.caracteristiques_actuelles()
