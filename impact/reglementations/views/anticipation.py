from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .tableau_de_bord import tableau_de_bord_menu_context
from .toutes_reglementations import etats_reglementations_selon_caracteristiques
from entreprises.decorators import entreprise_requise
from reglementations.forms.anticipation import AnticipationForm


@login_required
@entreprise_requise
def anticiper(request, entreprise):
    if request.POST:
        form = AnticipationForm(request.POST, entreprise=entreprise)
        if form.is_valid():
            actualisation_caracs = form.caracteristiques_anticipees()
            caracs = entreprise.actualise_caracteristiques(actualisation_caracs)
            reglementations = etats_reglementations_selon_caracteristiques(caracs)
            context = tableau_de_bord_menu_context(entreprise)
            context.update(reglementations)
            context["anticipation"] = True
            return render(
                request,
                "reglementations/tableau_de_bord/reglementations.html",
                context=context,
            )
        else:
            messages.error(
                request,
                "Impossible de finaliser cet essai car le formulaire contient des erreurs.",
            )
    else:
        caracs = entreprise.dernieres_caracteristiques_qualifiantes
        form = AnticipationForm(
            instance=caracs,
            initial={
                "est_cotee": entreprise.est_cotee,
                "est_interet_public": entreprise.est_interet_public,
                "appartient_groupe": entreprise.appartient_groupe,
                "est_societe_mere": entreprise.est_societe_mere,
                "societe_mere_en_france": entreprise.societe_mere_en_france,
                "comptes_consolides": entreprise.comptes_consolides,
            },
        )
    context = tableau_de_bord_menu_context(entreprise)
    context["form"] = form
    return render(
        request,
        "reglementations/tableau_de_bord/anticipation.html",
        context=context,
    )
