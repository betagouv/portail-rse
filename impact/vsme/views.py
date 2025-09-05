from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import Http404
from django.http.response import HttpResponseForbidden
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls.base import reverse

from entreprises.models import Entreprise
from entreprises.views import get_current_entreprise
from vsme.factory import create_form_from_schema
from vsme.factory import load_json_schema
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


def indicateurs_vsme(request, siren):
    entreprise = Entreprise.objects.get(siren=siren)
    context = {"entreprise": entreprise}
    return render(request, "vsme/indicateurs.html", context=context)


def indicateurs_vsme_categorie(request, siren, categorie):
    entreprise = Entreprise.objects.get(siren=siren)
    if categorie in (
        "informations-generales",
        "environnement",
        "social",
        "gouvernance",
    ):
        template_name = f"categories/{categorie}.html"
    else:
        raise Http404("Catégorie VSME inconnue")
    context = {"entreprise": entreprise}
    return render(request, template_name, context=context)


def exigence_de_publication(request, siren):
    entreprise = Entreprise.objects.get(siren=siren)
    rapport_vsme, created = RapportVSME.objects.get_or_create(
        entreprise=entreprise, annee=2024
    )
    schema = load_json_schema("schemas/B1.json")
    indicateurs = [dict(indicateur, id=id) for id, indicateur in schema.items()]
    context = {
        "entreprise": entreprise,
        "rapport_vsme": rapport_vsme,
        "indicateurs": indicateurs,
    }
    return render(request, "vsme/exigence_de_publication.html", context=context)


def indicateur_vsme(request, vsme_id, indicateur_schema_id):
    rapport_vsme = RapportVSME.objects.get(id=vsme_id)
    try:
        indicateur = rapport_vsme.indicateurs.get(schema_id=indicateur_schema_id)
    except ObjectDoesNotExist:
        indicateur = None
    exigence_de_publication = indicateur_schema_id.split("-")[0]
    schema = load_json_schema(f"schemas/{exigence_de_publication}.json")

    if request.method == "POST":
        form = create_form_from_schema(schema, indicateur_schema_id)(
            request.POST,
            initial=indicateur.data if indicateur else None,
        )
        if form.is_valid():
            if indicateur:
                indicateur.data = form.cleaned_data
                indicateur.save()
            else:
                rapport_vsme.indicateurs.create(
                    schema_id=indicateur_schema_id, data=form.cleaned_data
                )
            return redirect(
                "vsme:indicateurs_vsme",
                siren=rapport_vsme.entreprise.siren,
            )
    else:  # GET
        form = create_form_from_schema(schema, indicateur_schema_id)(
            initial=indicateur.data if indicateur else None
        )

    context = {
        "entreprise": rapport_vsme.entreprise,
        "form": form,
        "schema_indicateur": schema[indicateur_schema_id],
    }
    return render(request, "vsme/saisie_indicateur.html", context=context)
