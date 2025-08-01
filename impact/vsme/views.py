from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http.response import Http404
from django.http.response import HttpResponseForbidden
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls.base import reverse

from entreprises.models import Entreprise
from entreprises.views import get_current_entreprise


ETAPES = {
    "introduction": "Introduction",
    "module_base": "Module de base",
    "module_narratif": "Module narratif",
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

from .models import IndicateurTableau, IndicateurNombre
@login_required
@est_membre
def etape_vsme(request, siren, etape):
    context = _base_context(etape)

    match etape:
        case "introduction":
            template_name = "etapes/introduction.html"
        case "module_base":
            template_name = "etapes/module-base.html"
        case "module_narratif":
            template_name = "etapes/module-narratif.html"
        case _:
            return Http404("Etape VSME inconnue")

    context |= {
        "lien": reverse("vsme:etape_vsme", kwargs={"siren": siren, "etape": etape}),
        "nom_entreprise": request._nom_entreprise,
        "siren": siren,
        "tableau_form": IndicateurTableau.objects.first(),
        "nombre_form": IndicateurNombre.objects.first(),
    }

    return render(request, template_name, context=context)
