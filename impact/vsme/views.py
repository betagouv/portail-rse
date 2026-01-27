from functools import wraps
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.http.response import Http404
from django.http.response import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls.base import reverse
from openpyxl import load_workbook

import utils.htmx as htmx
from entreprises.decorators import entreprise_qualifiee_requise
from entreprises.models import Entreprise
from entreprises.views import get_current_entreprise
from habilitations.models import Habilitation
from logs import event_logger
from reglementations.views import tableau_de_bord_menu_context
from utils.xlsx import xlsx_response
from vsme.export import export_exigence_de_publication
from vsme.forms import create_multiform_from_schema
from vsme.forms import NON_PERTINENT_FIELD_NAME
from vsme.models import ajoute_donnes_calculees
from vsme.models import annee_est_valide
from vsme.models import Categorie
from vsme.models import ExigenceDePublication
from vsme.models import EXIGENCES_DE_PUBLICATION
from vsme.models import get_annee_max_valide
from vsme.models import get_annee_rapport_par_defaut
from vsme.models import get_annees_valides
from vsme.models import Indicateur
from vsme.models import RapportVSME


ETAPES = {
    "introduction": "Introduction",
    "module_base": "Module de base",
    "module_complet": "Module complet",
}


def _base_context(etape):
    return {
        "etape_courante": etape,
        "titre": ETAPES[etape],
        "etapes": ETAPES,
    }


# TODO: renforcer et mutualiser les permissions une fois les habilitations v2 fusionnées
def est_membre(func):
    # ne peut actuellement être utilisé que sur des fonctions avec
    # 2 params siren et etape
    @wraps(func)
    def _inner(request, siren=None, etape="introduction"):
        if not siren:
            entreprise = get_current_entreprise(request)
            if not entreprise:
                messages.warning(
                    request,
                    "Commencez par ajouter une entreprise à votre compte utilisateur avant d'accéder à l'espace VSME",
                )
                return redirect("entreprises:entreprises")
            return redirect("vsme:etape_vsme", siren=entreprise.siren, etape=etape)
        try:
            entreprise = Entreprise.objects.get(siren=siren)
            if request.user not in entreprise.users.all():
                return HttpResponseForbidden(
                    "L'utilisateur n'est pas membre de cette entreprise"
                )
        except Entreprise.DoesNotExist:
            return Http404("Cette entreprise n'existe pas")

        # autant réutiliser l'entreprise
        request._nom_entreprise = entreprise.denomination

        return func(request, siren, etape)

    return _inner


@login_required
@est_membre
def etape_vsme(request, siren, etape):
    try:
        context = _base_context(etape)
    except KeyError:  # l'étape n'existe pas
        raise Http404("Etape VSME inconnue")

    match etape:
        case "introduction":
            template_name = "etapes/introduction.html"
        case "module_base":
            template_name = "etapes/module-base.html"
        case "module_complet":
            template_name = "etapes/module-complet.html"

    context |= {
        "lien": reverse("vsme:etape_vsme", kwargs={"siren": siren, "etape": etape}),
        "nom_entreprise": request._nom_entreprise,
        "siren": siren,
    }

    # note : exemple de log en base
    event_logger.info(
        "view:vsme", {"etape": etape, "siren": siren, "idUtilisateur": request.user.pk}
    )

    return render(request, template_name, context=context)


@login_required
@entreprise_qualifiee_requise
def categories_vsme(request, entreprise_qualifiee, annee=None):
    if htmx.is_htmx(request):
        annee = request.GET["annee"]
        redirect_to = reverse(
            "vsme:categories_vsme",
            args=[entreprise_qualifiee.siren, annee],
        )
        return htmx.HttpResponseHXRedirect(redirect_to)

    annee_par_defaut = get_annee_rapport_par_defaut(entreprise_qualifiee)
    annee = annee or annee_par_defaut

    # Vérifier que l'année est valide pour cette entreprise
    if not annee_est_valide(annee, entreprise_qualifiee):
        messages.error(
            request,
            f"L'année {annee} n'est pas valide pour un rapport VSME. "
            f"Les rapports doivent être créés pour une année entre 2020 et {get_annee_max_valide(entreprise_qualifiee)}.",
        )
        return redirect("vsme:categories_vsme", siren=entreprise_qualifiee.siren)

    rapport_vsme, created = RapportVSME.objects.get_or_create(
        entreprise=entreprise_qualifiee, annee=annee
    )

    # Message informatif lors du changement d'année
    # On affiche le message si l'année n'est pas l'année par défaut
    # ou si l'utilisateur vient de créer un nouveau rapport
    if annee != annee_par_defaut or created:
        if annee == annee_par_defaut:
            messages.info(
                request,
                f"Vous travaillez sur le rapport VSME de l'année {annee} (année par défaut).",
            )
        else:
            messages.info(
                request, f"Vous travaillez sur le rapport VSME de l'année {annee}."
            )

    context = tableau_de_bord_menu_context(entreprise_qualifiee)
    context |= {
        "rapport_vsme": rapport_vsme,
        "annee_courante": annee,
        "annees_disponibles": get_annees_valides(entreprise_qualifiee),
        "annee_par_defaut": annee_par_defaut,
    }
    return render(request, "vsme/categories.html", context=context)


def rapport_vsme_requis(function):
    @wraps(function)
    def wrap(request, vsme_id, *args, **kwargs):
        rapport_vsme = get_object_or_404(RapportVSME, id=vsme_id)

        if not Habilitation.existe(rapport_vsme.entreprise, request.user):
            raise PermissionDenied()

        return function(request, rapport_vsme, *args, **kwargs)

    return wrap


@login_required
@rapport_vsme_requis
def categorie_vsme(request, rapport_vsme, categorie_id):
    categorie = Categorie.par_id(categorie_id)
    if not categorie:
        raise Http404("Catégorie VSME inconnue")
    exigences_de_publication_applicables = (
        rapport_vsme.exigences_de_publication_applicables()
    )
    exigences_de_publication = categorie.exigences_de_publication()
    for exigence in exigences_de_publication:
        exigence.est_applicable = exigence in exigences_de_publication_applicables
    context = tableau_de_bord_menu_context(rapport_vsme.entreprise)
    context |= {
        "rapport_vsme": rapport_vsme,
        "categorie": categorie,
        "exigences_de_publication": exigences_de_publication,
    }
    return render(request, "vsme/categorie.html", context=context)


@login_required
@rapport_vsme_requis
def exigence_de_publication_vsme(request, rapport_vsme, exigence_de_publication_code):
    exigence_de_publication = EXIGENCES_DE_PUBLICATION.get(exigence_de_publication_code)
    if not exigence_de_publication or not exigence_de_publication.remplissable:
        raise Http404("Exigence de publication VSME inconnue")
    indicateurs_completes = rapport_vsme.indicateurs_completes(exigence_de_publication)
    indicateurs_applicables = rapport_vsme.indicateurs_applicables(
        exigence_de_publication
    )
    exigence_de_publication_schema = exigence_de_publication.load_json_schema()
    indicateurs = [
        dict(
            indicateur,
            id=id,
            est_complete=id in indicateurs_completes,
            est_applicable=id in indicateurs_applicables,
        )
        for id, indicateur in exigence_de_publication_schema.items()
    ]

    context = tableau_de_bord_menu_context(rapport_vsme.entreprise)
    context |= {
        "rapport_vsme": rapport_vsme,
        "exigence_de_publication": exigence_de_publication,
        "indicateurs": indicateurs,
    }
    return render(request, "vsme/exigence_de_publication.html", context=context)


class IndicateurInconnu(Exception):
    pass


@login_required
@rapport_vsme_requis
def indicateur_vsme(request, rapport_vsme, indicateur_schema_id):
    try:
        indicateur_schema = load_indicateur_schema(indicateur_schema_id)
    except IndicateurInconnu:
        raise Http404("Indicateur VSME inconnu")

    exigence_de_publication = ExigenceDePublication.par_indicateur_schema_id(
        indicateur_schema_id
    )
    indicateur_est_applicable, explication_non_applicable = (
        rapport_vsme.indicateur_est_applicable(indicateur_schema_id)
    )

    try:
        indicateur = rapport_vsme.indicateurs.get(schema_id=indicateur_schema_id)
    except ObjectDoesNotExist:
        indicateur = None

    if request.method == "POST":
        if not indicateur_est_applicable:
            raise PermissionDenied()
        if delete_field_name := request.POST.get("supprimer-ligne"):
            data = request.POST.copy()
            data[delete_field_name] = True
        else:
            data = request.POST

        multiform = create_multiform_from_schema(indicateur_schema, rapport_vsme)(
            data,
            initial=indicateur.data if indicateur else None,
        )

        if "enregistrer" in request.POST:
            if multiform.is_valid():
                if indicateur:
                    indicateur.data = multiform.cleaned_data
                else:
                    indicateur = Indicateur(
                        rapport_vsme=rapport_vsme,
                        schema_id=indicateur_schema_id,
                        data=multiform.cleaned_data,
                    )
                indicateur.save()
                redirect_to = reverse(
                    "vsme:exigence_de_publication_vsme",
                    args=[rapport_vsme.id, exigence_de_publication.code],
                )
                if htmx.is_htmx(request):
                    return htmx.HttpResponseHXRedirect(redirect_to)
        elif "ajouter-ligne" in request.POST:
            if multiform.is_valid():
                data = ajoute_donnes_calculees(
                    indicateur_schema_id, rapport_vsme, multiform.cleaned_data
                )
                data, ligne_ajoutee = ajoute_auto_id_eventuel(indicateur_schema, data)
                multiform = create_multiform_from_schema(
                    indicateur_schema,
                    rapport_vsme,
                    id_tableau_ligne_ajoutee=request.POST["ajouter-ligne"],
                    ajoute_ligne_vide=not ligne_ajoutee,
                )(initial=data)
        elif "supprimer-ligne" in request.POST:
            if multiform.is_valid():
                data = ajoute_donnes_calculees(
                    indicateur_schema_id, rapport_vsme, multiform.cleaned_data
                )
                multiform = create_multiform_from_schema(
                    indicateur_schema,
                    rapport_vsme,
                )(initial=data)
        else:
            # un champ a déclenché un raffraichissement dynamique du formulaire (non pertinent, calcul...)
            if multiform.is_valid():
                data = ajoute_donnes_calculees(
                    indicateur_schema_id, rapport_vsme, multiform.cleaned_data
                )

            # Réinstancie le formulaire avec un initial mais sans data liée pour éviter de la validation et affichage d'erreurs
            multiform = create_multiform_from_schema(
                indicateur_schema,
                rapport_vsme,
            )(initial=data)

    else:  # GET
        infos_preremplissage = None
        data = indicateur.data if indicateur else {}
        if not data:
            data, _ = ajoute_auto_id_eventuel(indicateur_schema, data)
            infos_preremplissage = preremplit_indicateur(
                indicateur_schema_id, rapport_vsme
            )
        multiform = create_multiform_from_schema(
            indicateur_schema,
            rapport_vsme,
            infos_preremplissage=infos_preremplissage,
        )(
            initial=data,
        )

        if not indicateur_est_applicable:
            multiform.disable_all_fields()

    context = {
        "entreprise": rapport_vsme.entreprise,
        "multiform": multiform,
        "indicateur_schema": indicateur_schema,
        "indicateur_schema_id": indicateur_schema_id,
        "indicateur_est_applicable": indicateur_est_applicable,
        "explication_non_applicable": explication_non_applicable,
        "rapport_vsme": rapport_vsme,
        "exigence_de_publication": exigence_de_publication,
    }
    return render(request, "fragments/indicateur.html", context=context)


def load_indicateur_schema(indicateur_schema_id):
    exigence_de_publication_code = indicateur_schema_id.split("-")[0]
    try:
        exigence_de_publication_schema = EXIGENCES_DE_PUBLICATION[
            exigence_de_publication_code
        ].load_json_schema()
        return dict(
            exigence_de_publication_schema[indicateur_schema_id],
            schema_id=indicateur_schema_id,
        )
    except KeyError:
        raise IndicateurInconnu()


def ajoute_auto_id_eventuel(indicateur_schema, data):
    data = data.copy()
    tableaux = [
        champ for champ in indicateur_schema["champs"] if champ["type"] == "tableau"
    ]
    if not tableaux:
        return data, False
    for tableau in tableaux:
        tableau_id = tableau["id"]
        colonnes = tableau["colonnes"]
        champ_auto_id = [
            champ["id"] for champ in colonnes if champ["type"] == "auto_id"
        ]
        if champ_auto_id:
            champ_auto_id = champ_auto_id[0]
            prochain_id = (
                1
                if not data.get(tableau_id)
                else data[tableau_id][-1][champ_auto_id] + 1
            )
            nouvelle_ligne = [{champ_auto_id: prochain_id}]
            data[tableau_id] = data.get(tableau_id, []) + nouvelle_ligne
            return data, True
        else:
            return data, False


def preremplit_indicateur(indicateur_schema_id, rapport_vsme):
    infos_preremplissage = {}
    match indicateur_schema_id:
        case "B1-24-e-i":  # indicateur forme juridique
            entreprise = rapport_vsme.entreprise
            if entreprise.categorie_juridique_sirene:
                forme_juridique = str(entreprise.categorie_juridique_sirene)[:2]
                infos_preremplissage["initial"] = {
                    "forme_juridique": forme_juridique,
                    "coopérative": forme_juridique in ("51", "63"),
                }
                infos_preremplissage["source"] = {
                    "nom": "l'Annuaire des Entreprise",
                    "url": "https://annuaire-entreprises.data.gouv.fr/",
                }
        case "B8-40" | "B10-42-b":
            # indicateur taux de rotation du personnel | écart rémunération hommes/femmes
            nombre_salaries = rapport_vsme.nombre_salaries()
            if nombre_salaries is None:
                pass
            elif nombre_salaries < 50 or (
                nombre_salaries < 150 and indicateur_schema_id == "B10-42-b"
            ):
                infos_preremplissage["initial"] = {
                    NON_PERTINENT_FIELD_NAME: True,
                }
                infos_preremplissage["source"] = {
                    "nom": "l'indicateur Nombre de salariés dans B1",
                    "url": reverse(
                        "vsme:exigence_de_publication_vsme",
                        args=[rapport_vsme.id, "B1"],
                    ),
                }
    return infos_preremplissage


@login_required
@rapport_vsme_requis
def export_vsme(request, rapport_vsme):
    chemin_xlsx = Path(settings.BASE_DIR, f"vsme/xlsx/VSME.xlsx")
    workbook = load_workbook(chemin_xlsx)

    # Les exigences de publications sont ajoutées au fur et à mesure de leur intégration sur le portail au template d'export_vsme
    codes_exigences_de_publication_exportables = (
        "B1",
        "B2",
        "B3",
        "B4",
        "B5",
        "B6",
        "B7",
        "B8",
        "B9",
        "B10",
        "B11",
        "C1",
        "C6",
        "C8",
        "C9",
    )

    exigences_de_publication_applicables = (
        rapport_vsme.exigences_de_publication_applicables()
    )
    for exigence_de_publication in exigences_de_publication_applicables:
        if exigence_de_publication.code in codes_exigences_de_publication_exportables:
            export_exigence_de_publication(
                exigence_de_publication, workbook, rapport_vsme
            )

    # supprime les onglets des exigences de publication non applicables
    codes_exigences_de_publication_applicables = [
        e.code for e in exigences_de_publication_applicables
    ]
    codes_exigences_de_publication_a_supprimer = [
        code
        for code in codes_exigences_de_publication_exportables
        if code not in codes_exigences_de_publication_applicables
    ]
    for code in codes_exigences_de_publication_a_supprimer:
        nom_onglet = code
        workbook.remove(workbook[nom_onglet])

    # adapte le texte présent dans une cellule du premier onglet
    if rapport_vsme.choix_module() == "complet":
        texte = "Module complet"
    else:
        texte = "Module de base"
    workbook[">>> "]["C13"] = texte

    return xlsx_response(workbook, "vsme.xlsx")
