from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse_lazy

from .forms import AjoutEntrepriseConseillerForm
from .forms import AnticipationForm
from .metriques import calculer_metriques_entreprise
from api.exceptions import APIError
from entreprises.decorators import entreprise_qualifiee_requise
from entreprises.decorators import entreprise_requise
from entreprises.models import CODE_PAYS_FRANCE
from entreprises.models import Entreprise
from habilitations.enums import UserRole
from habilitations.models import Habilitation
from habilitations.models import HabilitationError
from habilitations.views import cree_invitation
from habilitations.views import utilisateurs_context
from logs import event_logger as logger
from logs import log_path
from reglementations.views.csrd.csrd import rapport_csrd
from reglementations.views.toutes_reglementations import (
    etats_reglementations_selon_caracteristiques,
)
from reglementations.views.toutes_reglementations import REGLEMENTATIONS
from utils.messages import message_error_sans_html
from utils.messages import message_success_sans_html
from utils.messages import message_warning_avec_html
from utils.messages import message_warning_sans_html
from vsme.models import RapportVSME


def tableau_de_bord_menu_context(entreprise, page_resume=False):
    return {
        "entreprise": entreprise,
        "page_resume": page_resume,
    }


@login_required
def redirection_tableau_de_bord_par_siren(request, siren):
    # les e-mails d'arrivée d'un nouveau membre envoyés avant le passage à l'id_public contiennent le SIREN
    entreprise = get_object_or_404(
        Entreprise, code_pays=CODE_PAYS_FRANCE, identifiant=siren
    )
    if not Habilitation.existe(entreprise, request.user):
        raise PermissionDenied
    return redirect("tableau_de_bord:tableau_de_bord", id_public=entreprise.id_public)


@login_required
@entreprise_requise
@log_path("app:tableauDeBord")
def tableau_de_bord(request, entreprise):
    caracteristiques = entreprise.dernieres_caracteristiques_qualifiantes

    # Afficher un avertissement si le profil est incomplet
    if not caracteristiques:
        url_qualification = reverse_lazy(
            "entreprises:qualification", args=[entreprise.id_public]
        )
        message_warning_avec_html(
            request,
            t"Votre profil entreprise est incomplet ou doit être mis à jour suite à l'évolution d'une réglementation. <a href='{url_qualification}'>Complétez-le pour avoir accès à toutes les fonctionnalités de votre tableau de bord.</a>",
        )
        nombre_reglementations_applicables = "?"
    else:
        # Afficher un avertissement si les caractéristiques ne sont pas à jour
        if caracteristiques != entreprise.caracteristiques_actuelles():
            url_qualification = reverse_lazy(
                "entreprises:qualification", args=[entreprise.id_public]
            )
            message_warning_avec_html(
                request,
                t"Les informations affichées sont basées sur l'exercice comptable {caracteristiques.annee}. <a href='{url_qualification}'>Mettre à jour le profil de l'entreprise.</a>",
            )

        # Calculer les réglementations applicables
        reglementations_applicables = [
            r for r in REGLEMENTATIONS if r.est_soumis(caracteristiques)
        ]
        nombre_reglementations_applicables = len(reglementations_applicables)

    # Calculer le nombre d'analyses IA réussies
    nombre_analyses_ia = (
        entreprise.analyses_ia.v1_reussies().count()
        + entreprise.analyses_ia.v2_reussies().count()
    )

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
    context |= utilisateurs_context(request, entreprise)
    context |= {
        "nombre_reglementations_applicables": nombre_reglementations_applicables,
        "nombre_analyses_ia": nombre_analyses_ia,
        "pourcentage_vsme": pourcentage_vsme,
    }

    return render(
        request,
        "tableau_de_bord/resume.html",
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
    return redirect("tableau_de_bord:tableau_de_bord", id_public=entreprise.id_public)


@login_required
@entreprise_requise
@log_path("app:tableauDeBord:rapport")
def rapport(request, entreprise):
    """Cette page n'est plus utilisée.

    On renvoie vers la page principale du tableau de bord plutôt qu'une 404 à un
    utilisateur viendrait sur cette page.
    """
    return redirect("tableau_de_bord:tableau_de_bord", id_public=entreprise.id_public)


def rapport_generique(request):
    """Cette page n'est plus utilisée maus l'URL pourrait être dans le site vitrine.

    On renvoie vers la page principale du tableau de bord plutôt qu'une 404 à un
    utilisateur viendrait sur cette page.
    Aucune vérification, la page suivante s'en charge.
    """
    return redirect("tableau_de_bord:tableau_de_bord")


@login_required
@entreprise_requise
@log_path("app:tableauDeBord:rapport:analyse_double_materialite")
def analyse_double_materialite(request, entreprise):
    context = tableau_de_bord_menu_context(entreprise)
    return render(
        request,
        "tableau_de_bord/analyse_double_materialite.html",
        context=context,
    )


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
        "tableau_de_bord/reglementations.html",
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

    template_name = f"tableau_de_bord/{id_reglementation}.html"

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
            "idEntreprise": entreprise.id,
            "session": request.session.session_key,
        },
    )

    return render(
        request,
        template_name,
        context=context,
    )


@login_required
@entreprise_requise
@log_path("app:tableauDeBord:anticiper")
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
                "tableau_de_bord/reglementations.html",
                context=context,
            )
        else:
            message_error_sans_html(
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
        "tableau_de_bord/anticipation.html",
        context=context,
    )


@login_required()
def tableau_de_bord_conseiller(request):
    """Tableau de bord pour les conseillers RSE.

    Gère l'ajout d'entreprise avec logique unifiée :
    - Entreprise existante avec administrateur : refus attachement
    - Entreprise existante sans administrateur : rattachement + invitation administrateur
    - Entreprise inexistante : création + rattachement + invitation administrateur
    """
    # Vérifier que l'utilisateur est bien un conseiller RSE
    if not request.user.is_conseiller_rse:
        message_error_sans_html(
            request,
            "Vous devez être identifié comme conseiller RSE pour accéder à cette page.",
        )
        return redirect("entreprises:entreprises")

    # Récupérer les entreprises en gestion
    habilitations = Habilitation.objects.filter(user=request.user).select_related(
        "entreprise"
    )

    # Enrichir chaque habilitation avec les metriques
    habilitations_enrichies = []
    for habilitation in habilitations:
        metriques = calculer_metriques_entreprise(habilitation.entreprise)
        habilitations_enrichies.append(
            {
                "habilitation": habilitation,
                "entreprise": habilitation.entreprise,
                "nombre_reglementations": metriques[
                    "nombre_reglementations_applicables"
                ],
                "pourcentage_vsme": metriques["pourcentage_vsme"],
            }
        )

    if request.method == "POST":
        form = AjoutEntrepriseConseillerForm(request.POST)
        if form.is_valid():
            try:
                siren = form.cleaned_data["siren"]
                email_administrateur = form.cleaned_data.get(
                    "email_futur_administrateur"
                )

                # CAS 1 : Entreprise existe
                if Entreprise.objects.filter(
                    code_pays=CODE_PAYS_FRANCE, identifiant=siren
                ).exists():
                    entreprise = Entreprise.objects.get(
                        code_pays=CODE_PAYS_FRANCE, identifiant=siren
                    )

                    # Vérifier si le conseiller n'est pas déjà rattaché
                    if Habilitation.existe(entreprise, request.user):
                        message_warning_sans_html(
                            request,
                            f"Vous êtes déjà rattaché à l'entreprise {entreprise.denomination}.",
                        )
                        return redirect("tableau_de_bord:tableau_de_bord_conseiller")

                    # CAS 1a : A un administrateur → pas de rattachement
                    if entreprise.administrateurs:
                        message_error_sans_html(
                            request,
                            f"Vous n'avez pas été rattaché à l'entreprise {entreprise.denomination} car un compte y est déjà attachée. Demandez à votre client de vous inviter sur l'entreprise.",
                        )
                        return redirect("tableau_de_bord:tableau_de_bord_conseiller")

                    # CAS 1b : Pas d'administrateur → rattachement + invitation
                    else:
                        Habilitation.ajouter(
                            entreprise,
                            request.user,
                            UserRole.ADMINISTRATEUR,
                            fonctions=form.cleaned_data.get("fonctions"),
                            is_conseiller_rse=True,
                        )
                        cree_invitation(
                            request,
                            entreprise,
                            email_administrateur,
                            UserRole.ADMINISTRATEUR,
                            template_id=settings.BREVO_INVITATION_CONSEILLER_RSE_TEMPLATE,
                        )
                        message_success_sans_html(
                            request,
                            f"Vous avez été rattaché à l'entreprise {entreprise.denomination}. "
                            f"Une invitation a été envoyée à {email_administrateur} pour devenir administrateur.",
                        )
                        return redirect("tableau_de_bord:tableau_de_bord_conseiller")

                # CAS 2 : Entreprise n'existe pas → création + rattachement + invitation
                else:
                    entreprise = Entreprise.search_and_create_entreprise(siren)
                    Habilitation.ajouter(
                        entreprise,
                        request.user,
                        UserRole.ADMINISTRATEUR,
                        fonctions=form.cleaned_data.get("fonctions"),
                        is_conseiller_rse=True,
                    )
                    cree_invitation(
                        request,
                        entreprise,
                        email_administrateur,
                        UserRole.ADMINISTRATEUR,
                        template_id=settings.BREVO_INVITATION_CONSEILLER_RSE_TEMPLATE,
                    )
                    message_success_sans_html(
                        request,
                        f"L'entreprise {entreprise.denomination} a été créée. "
                        f"Une invitation a été envoyée à {email_administrateur} pour devenir administrateur.",
                    )
                    return redirect("tableau_de_bord:tableau_de_bord_conseiller")

            except APIError as exception:
                message_error_sans_html(request, str(exception))
            except HabilitationError as exception:
                message_error_sans_html(request, str(exception))
        else:
            message_error_sans_html(request, "Le formulaire est incomplet.")
    else:
        form = AjoutEntrepriseConseillerForm()

    return render(
        request,
        "tableau_de_bord/conseiller.html",
        {"habilitations_enrichies": habilitations_enrichies, "form": form},
    )
