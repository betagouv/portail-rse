from datetime import date
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse_lazy

from entreprises.decorators import entreprise_requise
from entreprises.models import CaracteristiquesAnnuelles
from habilitations.views import contributeurs_context
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


def tableau_de_bord_menu_context(entreprise, page_resume=False):
    return {
        "entreprise": entreprise,
        "page_resume": page_resume,
        "annee_precedente": date.today().year - 1,
    }


@login_required
@entreprise_requise
def tableau_de_bord(request, entreprise):
    caracteristiques = (
        entreprise.dernieres_caracteristiques_qualifiantes
        or entreprise.dernieres_caracteristiques
    )

    # Gérer le cas où il n'y a aucune caractéristique
    if not caracteristiques:
        messages.warning(
            request,
            "Veuillez renseigner le profil de l'entreprise pour accéder au tableau de bord.",
        )
        return redirect("entreprises:qualification", siren=entreprise.siren)

    # Afficher un message d'info si le profil est incomplet
    if not caracteristiques.sont_qualifiantes:
        messages.info(
            request,
            f"Le profil de votre entreprise est incomplet. Certaines réglementations ne pourront pas être calculées. "
            f"<a href='{reverse_lazy('entreprises:qualification', args=[entreprise.siren])}'>Compléter le profil</a>",
        )
    # Afficher un avertissement si les caractéristiques ne sont pas à jour
    elif caracteristiques != entreprise.caracteristiques_actuelles():
        messages.warning(
            request,
            f"Les informations affichées sont basées sur l'exercice comptable {caracteristiques.annee}. <a href='{reverse_lazy('entreprises:qualification', args=[entreprise.siren])}'>Mettre à jour le profil de l'entreprise.</a>",
        )

    # Calculer les réglementations applicables (peut lever des exceptions pour certaines)
    reglementations_applicables = []
    for reglementation in REGLEMENTATIONS:
        try:
            if reglementation.est_soumis(caracteristiques):
                reglementations_applicables.append(reglementation)
        except Exception:
            # Si on ne peut pas calculer, on ignore cette réglementation
            pass

    nombre_reglementations_applicables = len(reglementations_applicables)

    context = tableau_de_bord_menu_context(entreprise, page_resume=True)
    context |= contributeurs_context(request, entreprise)
    context |= {
        "nombre_reglementations_applicables": nombre_reglementations_applicables
    }

    return render(
        request,
        "reglementations/tableau_de_bord/resume.html",
        context=context,
    )


@login_required
@entreprise_requise
def reglementations(request, entreprise):
    caracteristiques = (
        entreprise.dernieres_caracteristiques_qualifiantes
        or entreprise.dernieres_caracteristiques
    )

    # Gérer le cas où il n'y a aucune caractéristique
    if not caracteristiques:
        messages.warning(
            request,
            "Veuillez renseigner le profil de l'entreprise pour accéder aux réglementations.",
        )
        return redirect("entreprises:qualification", siren=entreprise.siren)

    # Afficher un message d'info si le profil est incomplet
    if not caracteristiques.sont_qualifiantes:
        messages.info(
            request,
            f"Le profil de votre entreprise est incomplet. Certaines réglementations ne pourront pas être calculées. "
            f"<a href='{reverse_lazy('entreprises:qualification', args=[entreprise.siren])}'>Compléter le profil</a>",
        )
    # Afficher un avertissement si les caractéristiques ne sont pas à jour
    elif caracteristiques != entreprise.caracteristiques_actuelles():
        messages.warning(
            request,
            f"Les informations affichées sont basées sur l'exercice comptable {caracteristiques.annee}. <a href='{reverse_lazy('entreprises:qualification', args=[entreprise.siren])}'>Mettre à jour le profil de l'entreprise.</a>",
        )

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
    reglementations_incalculables = [
        r
        for r in reglementations
        if r["status"].status == ReglementationStatus.STATUS_INCALCULABLE
    ]

    context = tableau_de_bord_menu_context(entreprise)
    context |= {
        "reglementations_a_actualiser": reglementations_a_actualiser,
        "reglementations_en_cours": reglementations_en_cours,
        "reglementations_a_jour": reglementations_a_jour,
        "autres_reglementations": reglementations_soumises
        + reglementations_recommandees
        + reglementations_non_soumises
        + reglementations_incalculables,
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
@entreprise_requise
def reglementation(request, entreprise, id_reglementation):
    reglementation = None
    for r in REGLEMENTATIONS:
        if r.id == id_reglementation:
            reglementation = r
            break
    if not reglementation:
        raise Http404

    caracteristiques = (
        entreprise.dernieres_caracteristiques_qualifiantes
        or entreprise.dernieres_caracteristiques
    )

    # Gérer le cas où il n'y a aucune caractéristique
    if not caracteristiques:
        messages.warning(
            request,
            "Veuillez renseigner le profil de l'entreprise pour voir cette réglementation.",
        )
        return redirect("entreprises:qualification", siren=entreprise.siren)

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

    return render(
        request,
        template_name,
        context=context,
    )
