from functools import wraps

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

import utils.htmx as htmx
from entreprises.decorators import entreprise_qualifiee_requise
from entreprises.models import Entreprise
from entreprises.views import get_current_entreprise
from habilitations.models import Habilitation
from vsme.forms import create_multiform_from_schema
from vsme.models import Categorie
from vsme.models import EXIGENCES_DE_PUBLICATION
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

    return render(request, template_name, context=context)


@login_required
@entreprise_qualifiee_requise
def indicateurs_vsme(request, entreprise_qualifiee, annee=None):
    annee = annee or 2024
    rapport_vsme, created = RapportVSME.objects.get_or_create(
        entreprise=entreprise_qualifiee, annee=annee
    )
    context = {
        "entreprise": entreprise_qualifiee,
        "rapport_vsme": rapport_vsme,
    }
    return render(request, "vsme/indicateurs.html", context=context)


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
    context = {
        "entreprise": rapport_vsme.entreprise,
        "rapport_vsme": rapport_vsme,
        "categorie": categorie,
    }
    return render(request, "vsme/categorie.html", context=context)


@login_required
@rapport_vsme_requis
def exigence_de_publication_vsme(request, rapport_vsme, exigence_de_publication_code):
    exigence_de_publication = EXIGENCES_DE_PUBLICATION.get(exigence_de_publication_code)
    if not exigence_de_publication or not exigence_de_publication.remplissable:
        raise Http404("Exigence de publication VSME inconnue")
    indicateurs_completes = rapport_vsme.indicateurs_completes(exigence_de_publication)
    indicateurs_actifs = rapport_vsme.indicateurs_actifs(exigence_de_publication)
    exigence_de_publication_schema = exigence_de_publication.load_json_schema()
    indicateurs = [
        dict(
            indicateur,
            id=id,
            est_complete=id in indicateurs_completes,
            est_actif=id in indicateurs_actifs,
        )
        for id, indicateur in exigence_de_publication_schema.items()
    ]

    context = {
        "entreprise": rapport_vsme.entreprise,
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

    try:
        indicateur = rapport_vsme.indicateurs.get(schema_id=indicateur_schema_id)
    except ObjectDoesNotExist:
        indicateur = None

    toggle_pertinent_url = reverse(
        "vsme:toggle_pertinent", args=[rapport_vsme.id, indicateur_schema_id]
    )

    if request.method == "POST":
        if delete_field_name := request.POST.get("supprimer-ligne"):
            data = request.POST.copy()
            data[delete_field_name] = True
        else:
            data = request.POST
        multiform = create_multiform_from_schema(
            indicateur_schema, toggle_pertinent_url=toggle_pertinent_url
        )(
            data,
            initial=indicateur.data if indicateur else None,
        )
        if multiform.is_valid():
            if indicateur:
                indicateur.data = multiform.cleaned_data
            else:
                indicateur = Indicateur(
                    rapport_vsme=rapport_vsme,
                    schema_id=indicateur_schema_id,
                    data=multiform.cleaned_data,
                )
            if "enregistrer" in request.POST:
                indicateur.save()
                exigence_de_publication = indicateur_schema_id.split("-")[0]
                redirect_to = reverse(
                    "vsme:exigence_de_publication_vsme",
                    args=[rapport_vsme.id, exigence_de_publication],
                )
                if htmx.is_htmx(request):
                    return htmx.HttpResponseHXRedirect(redirect_to)
            else:
                extra = 0
                data = indicateur.data.copy()
                if request.POST.get("ajouter-ligne"):
                    if indicateur_a_champ_auto_id(indicateur_schema):
                        tableau, champ_auto_id = indicateur_a_champ_auto_id(
                            indicateur_schema
                        )
                        prochain_id = (
                            1
                            if not indicateur.data.get(tableau)
                            else indicateur.data[tableau][-1][champ_auto_id] + 1
                        )
                        nouvelle_ligne = [{champ_auto_id: prochain_id}]
                        data[tableau] = data[tableau] + nouvelle_ligne
                    else:
                        extra = 1
                multiform = calcule_indicateur(
                    indicateur_schema,
                    toggle_pertinent_url,
                    data,
                    extra=extra,
                )

    else:  # GET
        data = indicateur.data if indicateur else None
        multiform = calcule_indicateur(indicateur_schema, toggle_pertinent_url, data)

    context = {
        "entreprise": rapport_vsme.entreprise,
        "multiform": multiform,
        "indicateur_schema": indicateur_schema,
        "indicateur_schema_id": indicateur_schema_id,
        "rapport_vsme": rapport_vsme,
    }
    return render(request, "fragments/indicateur.html", context=context)


def load_indicateur_schema(indicateur_schema_id):
    exigence_de_publication_code = indicateur_schema_id.split("-")[0]
    try:
        exigence_de_publication_schema = EXIGENCES_DE_PUBLICATION[
            exigence_de_publication_code
        ].load_json_schema()
        return exigence_de_publication_schema[indicateur_schema_id]
    except KeyError:
        raise IndicateurInconnu()


def indicateur_a_champ_auto_id(indicateur_schema):
    tableaux = [
        champ for champ in indicateur_schema["champs"] if champ["type"] == "tableau"
    ]
    if not tableaux:
        return False
    for tableau in tableaux:
        tableau_id = tableau["id"]
        colonnes = tableau["colonnes"]
        champ_auto_id = [
            champ["id"] for champ in colonnes if champ["type"] == "auto_id"
        ]
        if champ_auto_id:
            return tableau_id, champ_auto_id[0]


@login_required
@rapport_vsme_requis
def toggle_pertinent(request, rapport_vsme, indicateur_schema_id):
    indicateur_schema = load_indicateur_schema(indicateur_schema_id)
    toggle_pertinent_url = reverse(
        "vsme:toggle_pertinent", args=[rapport_vsme.id, indicateur_schema_id]
    )
    multiform = calcule_indicateur(
        indicateur_schema, toggle_pertinent_url, request.POST
    )

    context = {
        "entreprise": rapport_vsme.entreprise,
        "multiform": multiform,
        "indicateur_schema": indicateur_schema,
        "indicateur_schema_id": indicateur_schema_id,
        "rapport_vsme": rapport_vsme,
    }
    return render(request, "fragments/indicateur.html", context=context)


def calcule_indicateur(indicateur_schema, toggle_pertinent_url, data, extra=0):
    multiform = create_multiform_from_schema(
        indicateur_schema, toggle_pertinent_url=toggle_pertinent_url, extra=extra
    )(
        initial=data,
    )
    return multiform
