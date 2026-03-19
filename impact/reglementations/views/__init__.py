from datetime import date
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse_lazy

from entreprises.decorators import entreprise_qualifiee_requise
from entreprises.decorators import entreprise_requise
from entreprises.models import CaracteristiquesAnnuelles
from habilitations.views import contributeurs_context
from logs import event_logger as logger
from logs import log_path
from reglementations.utils import VSMEReglementation
from reglementations.views.audit_energetique import AuditEnergetiqueReglementation
from reglementations.views.base import ReglementationStatus
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.bges import BGESReglementation
from reglementations.views.csrd import CSRDReglementation
from reglementations.views.csrd.csrd import rapport_csrd
from reglementations.views.dispositif_alerte import DispositifAlerteReglementation
from reglementations.views.dispositif_anticorruption import DispositifAntiCorruption
from reglementations.views.index_egapro import IndexEgaproReglementation
from reglementations.views.plan_vigilance import PlanVigilanceReglementation
from vsme.models import RapportVSME


REGLEMENTATIONS = [
    VSMEReglementation,
    CSRDReglementation,
    BDESEReglementation,
    IndexEgaproReglementation,
    DispositifAlerteReglementation,
    BGESReglementation,
    AuditEnergetiqueReglementation,
    DispositifAntiCorruption,
    PlanVigilanceReglementation,
]


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
    annee_precedente = date.today().year - 1
    try:
        rapport_vsme = RapportVSME.objects.get(
            entreprise=entreprise, annee=annee_precedente
        )
        pourcentage_vsme = rapport_vsme.progression()["pourcent"]
    except RapportVSME.DoesNotExist:
        pourcentage_vsme = 0

    return {
        "nombre_reglementations_applicables": nombre_reglementations_applicables,
        "pourcentage_vsme": pourcentage_vsme,
    }


def tableau_de_bord_menu_context(entreprise, page_resume=False):
    return {
        "entreprise": entreprise,
        "page_resume": page_resume,
        "annee_precedente": date.today().year - 1,
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
            f"Le profil de votre entreprise est incomplet. Certaines réglementations ne peuvent pas être calculées. <a href='{reverse_lazy('entreprises:qualification', args=[entreprise.siren])}'>Compléter le profil.</a>"
            f"",
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
    annee_precedente = date.today().year - 1
    try:
        rapport_vsme = RapportVSME.objects.get(
            entreprise=entreprise, annee=annee_precedente
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
    context = tableau_de_bord_menu_context(entreprise)
    return render(
        request,
        "reglementations/tableau_de_bord/index.html",
        context=context,
    )


@login_required
@entreprise_requise
@log_path("app:tableauDeBord:rapport")
def rapport(request, entreprise):
    context = tableau_de_bord_menu_context(entreprise)
    return render(
        request,
        "reglementations/tableau_de_bord/rapport.html",
        context=context,
    )


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


@login_required
@entreprise_qualifiee_requise
@log_path("app:reglementations")
def reglementations(request, entreprise):
    caracteristiques = entreprise.dernieres_caracteristiques_qualifiantes

    reglementations = calcule_reglementations(caracteristiques)
    reglementations_a_actualiser = [
        r
        for r in reglementations
        if r["status"].status == ReglementationStatus.STATUS_A_ACTUALISER
    ]
    reglementations_en_cours = [
        r
        for r in reglementations
        if r["status"].status == ReglementationStatus.STATUS_EN_COURS
    ]
    reglementations_a_jour = [
        r
        for r in reglementations
        if r["status"].status == ReglementationStatus.STATUS_A_JOUR
    ]
    reglementations_soumises = [
        r
        for r in reglementations
        if r["status"].status == ReglementationStatus.STATUS_SOUMIS
    ]
    reglementations_non_soumises = [
        r
        for r in reglementations
        if r["status"].status == ReglementationStatus.STATUS_NON_SOUMIS
    ]
    reglementations_recommandees = [
        r
        for r in reglementations
        if r["status"].status == ReglementationStatus.STATUS_RECOMMANDE
    ]

    context = tableau_de_bord_menu_context(entreprise)
    context |= {
        "reglementations_a_actualiser": reglementations_a_actualiser,
        "reglementations_en_cours": reglementations_en_cours,
        "reglementations_a_jour": reglementations_a_jour,
        "autres_reglementations": reglementations_soumises
        + reglementations_recommandees
        + reglementations_non_soumises,
    }
    return render(
        request,
        "reglementations/tableau_de_bord/reglementations.html",
        context=context,
    )


def calcule_reglementations(caracteristiques: CaracteristiquesAnnuelles):
    reglementations = [
        {
            "reglementation": reglementation,
            "status": reglementation.calculate_status(caracteristiques),
        }
        for reglementation in REGLEMENTATIONS
    ]
    return reglementations


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
