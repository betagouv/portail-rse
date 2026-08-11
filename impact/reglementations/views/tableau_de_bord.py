from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse_lazy

from .toutes_reglementations import REGLEMENTATIONS
from entreprises.decorators import entreprise_requise
from habilitations.views import contributeurs_context
from logs import log_path
from vsme.models import RapportVSME


def tableau_de_bord_menu_context(entreprise, page_resume=False):
    return {
        "entreprise": entreprise,
        "page_resume": page_resume,
    }


@login_required
@entreprise_requise
@log_path("app:tableauDeBord")
def tableau_de_bord(request, entreprise):
    caracteristiques = entreprise.dernieres_caracteristiques_qualifiantes

    # Afficher un avertissement si le profil est incomplet
    if not caracteristiques:
        messages.warning(
            request,
            f"Votre profil entreprise est incomplet ou doit être mis à jour suite à l'évolution d'une réglementation. <a href='{reverse_lazy('entreprises:qualification', args=[entreprise.siren])}'>Complétez-le pour avoir accès à toutes les fonctionnalités de votre tableau de bord.</a>",
        )
        nombre_reglementations_applicables = "?"
    else:
        # Afficher un avertissement si les caractéristiques ne sont pas à jour
        if caracteristiques != entreprise.caracteristiques_actuelles():
            messages.warning(
                request,
                f"Les informations affichées sont basées sur l'exercice comptable {caracteristiques.annee}. <a href='{reverse_lazy('entreprises:qualification', args=[entreprise.siren])}'>Mettre à jour le profil de l'entreprise.</a>",
            )

        # Calculer les réglementations applicables
        reglementations_applicables = [
            r for r in REGLEMENTATIONS if r.est_soumis(caracteristiques)
        ]
        nombre_reglementations_applicables = len(reglementations_applicables)

    # Calculer le nombre d'analyses IA réussies
    nombre_analyses_ia = entreprise.analyses_ia.reussies().count()

    # Calculer le pourcentage de progression VSME
    try:
        rapport_vsme = RapportVSME.objects.get(
            entreprise=entreprise,
            annee=entreprise.dernier_exercice_clos.date_cloture.year,
        )
        pourcentage_vsme = rapport_vsme.progression()["pourcent"]
    except RapportVSME.DoesNotExist:
        pourcentage_vsme = 0

    context = tableau_de_bord_menu_context(entreprise, page_resume=True)
    context |= contributeurs_context(request, entreprise)
    context |= {
        "nombre_reglementations_applicables": nombre_reglementations_applicables,
        "nombre_analyses_ia": nombre_analyses_ia,
        "pourcentage_vsme": pourcentage_vsme,
    }

    return render(
        request,
        "reglementations/tableau_de_bord/resume.html",
        context=context,
    )


@login_required
@entreprise_requise
@log_path("app:tableauDeBord:index")
def index(request, entreprise):
    """Cette page n'est plus utilisée.

    On renvoie vers la page principale du tableau de bord plutôt qu'une 404 à un
    utilisateur viendrait sur cette page.
    """
    return redirect("reglementations:tableau_de_bord", siren=entreprise.siren)


@login_required
@entreprise_requise
@log_path("app:tableauDeBord:rapport")
def rapport(request, entreprise):
    """Cette page n'est plus utilisée.

    On renvoie vers la page principale du tableau de bord plutôt qu'une 404 à un
    utilisateur viendrait sur cette page.
    """
    return redirect("reglementations:tableau_de_bord", siren=entreprise.siren)


def rapport_generique(request):
    """Cette page n'est plus utilisée maus l'URL pourrait être dans le site vitrine.

    On renvoie vers la page principale du tableau de bord plutôt qu'une 404 à un
    utilisateur viendrait sur cette page.
    Aucune vérification, la page suivante s'en charge.
    """
    return redirect("reglementations:tableau_de_bord")


@login_required
@entreprise_requise
@log_path("app:tableauDeBord:rapport:analyse_double_materialite")
def analyse_double_materialite(request, entreprise):
    context = tableau_de_bord_menu_context(entreprise)
    return render(
        request,
        "reglementations/tableau_de_bord/analyse_double_materialite.html",
        context=context,
    )
