from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import render

from .tableau_de_bord import tableau_de_bord_menu_context
from .toutes_reglementations import etats_reglementations_selon_caracteristiques
from .toutes_reglementations import REGLEMENTATIONS
from entreprises.decorators import entreprise_qualifiee_requise
from logs import event_logger as logger
from logs import log_path
from reglementations.views.csrd.csrd import rapport_csrd
from vsme.models import RapportVSME


def calculer_metriques_entreprise(entreprise):
    """Calcule les metriques synthetiques pour une entreprise.

    Returns:
        dict: {
            'nombre_reglementations_applicables': int | "?",
            'pourcentage_vsme': int
        }
    """
    # Recuperer les caracteristiques actuelles
    caracteristiques = entreprise.dernieres_caracteristiques_qualifiantes

    # Calcul du nombre de reglementations applicables
    if caracteristiques:
        reglementations_applicables = [
            r for r in REGLEMENTATIONS if r.est_soumis(caracteristiques)
        ]
        nombre_reglementations_applicables = len(reglementations_applicables)
    else:
        nombre_reglementations_applicables = "?"

    # Calcul du pourcentage VSME
    try:
        rapport_vsme = RapportVSME.objects.get(
            entreprise=entreprise,
            annee=entreprise.dernier_exercice_clos.date_cloture.year,
        )
        pourcentage_vsme = rapport_vsme.progression()["pourcent"]
    except RapportVSME.DoesNotExist:
        pourcentage_vsme = 0

    return {
        "nombre_reglementations_applicables": nombre_reglementations_applicables,
        "pourcentage_vsme": pourcentage_vsme,
    }


@login_required
@entreprise_qualifiee_requise
@log_path("app:reglementations")
def reglementations(request, entreprise):
    caracteristiques = entreprise.dernieres_caracteristiques_qualifiantes
    reglementations = etats_reglementations_selon_caracteristiques(caracteristiques)
    context = tableau_de_bord_menu_context(entreprise)
    context.update(reglementations)
    return render(
        request,
        "reglementations/tableau_de_bord/reglementations.html",
        context=context,
    )


@login_required
@entreprise_qualifiee_requise
def reglementation(request, entreprise, id_reglementation):
    reglementation = None
    for r in REGLEMENTATIONS:
        if r.id == id_reglementation:
            reglementation = r
            break
    if not reglementation:
        raise Http404

    caracteristiques = entreprise.dernieres_caracteristiques_qualifiantes
    status = reglementation.calculate_status(caracteristiques)

    template_name = f"reglementations/tableau_de_bord/{id_reglementation}.html"

    context = tableau_de_bord_menu_context(entreprise)
    context |= {
        "reglementation": reglementation,
        "status": status,
    }
    if id_reglementation == "csrd":
        try:
            rapport = rapport_csrd(
                entreprise=entreprise,
                annee=datetime.today().year,
            )
        except ObjectDoesNotExist:
            rapport = None
        context["csrd"] = rapport

    logger.info(
        f"app:reglementation:{id_reglementation}",
        {
            "idUtilisateur": request.user.pk,
            "siren": request.session["entreprise"],
            "session": request.session.session_key,
        },
    )

    return render(
        request,
        template_name,
        context=context,
    )
