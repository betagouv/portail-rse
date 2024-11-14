"""
Fragments HTMX pour la sélection des enjeux par ESRS
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.shortcuts import HttpResponse
from django.shortcuts import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

import utils.htmx as htmx
from reglementations.enums import ESRS
from reglementations.enums import ThemeESRS
from reglementations.enums import TitreESRS
from reglementations.forms.csrd import EnjeuxRapportCSRDForm
from reglementations.forms.csrd import NouvelEnjeuCSRDForm
from reglementations.models.csrd import Enjeu
from reglementations.models.csrd import RapportCSRD

"""
Vues de fragments HTMX :
    Optimisation du format et de la taille des réponses.
"""


def csrd_required(function):
    @wraps(function)
    def wrap(request, csrd_id, *args, **kwargs):
        csrd = get_object_or_404(RapportCSRD, id=csrd_id)

        if not csrd.modifiable_par(request.user):
            raise PermissionDenied(
                "L'utilisateur n'a pas les permissions nécessaires pour accéder à ce rapport CSRD"
            )
        return function(request, csrd_id, *args, **kwargs)

    return wrap


def enjeu_required(function):
    @wraps(function)
    def wrap(request, enjeu_id, *args, **kwargs):
        enjeu = get_object_or_404(Enjeu, pk=enjeu_id)

        if not enjeu.rapport_csrd.modifiable_par(request.user):
            raise PermissionDenied(
                "L'utilisateur n'a pas les permissions nécessaires pour accéder à ce rapport CSRD"
            )
        return function(request, enjeu_id, *args, **kwargs)

    return wrap


@login_required
@csrd_required
@require_http_methods(["GET", "POST"])
def selection_enjeux(request, csrd_id, esrs):
    csrd = RapportCSRD.objects.get(id=csrd_id)

    context = {"csrd": csrd}

    if request.method == "GET":
        return render(
            request,
            template_name="fragments/selection_enjeux.html",
            context=context | {"form": EnjeuxRapportCSRDForm(instance=csrd, esrs=esrs)},
        )

    # Dans un fragment, l'utilisation du Post/Redirect/Get n'est pas nécessaire (XHR)
    form = EnjeuxRapportCSRDForm(request.POST, instance=csrd, esrs=esrs)

    if form.is_valid():
        form.save()

    return render(
        request,
        "fragments/esrs.html",
        context=context,
    )


@login_required
@csrd_required
@require_http_methods(["GET", "POST"])
def creation_enjeu(request, csrd_id, esrs):
    csrd = RapportCSRD.objects.get(id=csrd_id)

    context = {"csrd": csrd}
    template = "fragments/creation_enjeu.html"

    if request.method == "GET":
        # cas 1 : ouverture du panel de création d'un enjeu
        form = NouvelEnjeuCSRDForm(instance=csrd, esrs=esrs)
        return render(request, template, context=context | {"form": form})

    form = NouvelEnjeuCSRDForm(request.POST, instance=csrd, esrs=esrs)

    if form.is_valid():
        # cas 2 : le formulaire est valide
        # on recharge le bloc création + sélection des enjeux en entier pour actualiser
        # c'est un cas un peu particulier (on veut changer la cible HTMX)
        # il y a un header prévu en HTMX : HX-Retarget,
        # mais un redirect ne transmettant pas les headers, on peut le faire passer
        # via différents moyens à la cible de la redirection.
        # Ici automatiquement traité automatiquement par un middleware.
        form.save()

        # indique que la réponse devra changer de cible HTMX
        params = htmx.retarget_params(request, "#selection_enjeux_" + esrs)

        return HttpResponseRedirect(
            redirect_to=reverse(
                "reglementations:selection_enjeux",
                kwargs={"csrd_id": csrd_id, "esrs": esrs},
            )
            + f"?{params}"
        )
    else:
        # cas 3 : erreurs dans le formulaire, on reste sur le fragment
        return render(request, template, context=context | {"form": form})


@login_required
@enjeu_required
@csrf_exempt
@require_http_methods(["POST"])
def deselection_enjeu(request, enjeu_id):
    # note : la vue est "exempté" de CSRF parce que ce fragment est "emboité" dans un formulaire
    # la session contient donc un token CSRF à vérifier ... qu'on ne veut pas vérifier dans ce cas.
    enjeu = Enjeu.objects.get(id=enjeu_id)

    enjeu.selection = False
    enjeu.save()

    # la chaine vide permet la suppression de l'enjeu dans l'interface web
    return HttpResponse(status=200, content="")


@login_required
@enjeu_required
@csrf_exempt
@require_http_methods(["DELETE"])
def suppression_enjeu(request, enjeu_id):
    # note : la vue est "exempté" de CSRF parce que ce fragment est "emboité" dans un formulaire
    # la session contient donc un token CSRF à vérifier ... qu'on ne veut pas vérifier dans ce cas.
    enjeu = Enjeu.objects.get(id=enjeu_id, modifiable=True)

    enjeu.delete()

    # on veut actualiser toute la sélection des enjeux,
    # pour faire disparaitre l'enjeu supprimé
    params = htmx.retarget_params(request, "#selection_enjeux_" + enjeu.esrs)

    # tip: redirection post `DELETE` :
    # on veux rediriger mais avec une méthode différente pour la cible (`GET`),
    # les redirections 302 sont inadaptées pour ça, il faut une 303.
    return HttpResponseRedirect(
        status=303,
        redirect_to=reverse(
            "reglementations:selection_enjeux",
            kwargs={"csrd_id": enjeu.rapport_csrd.pk, "esrs": enjeu.esrs},
        )
        + f"?{params}",
    )


def rafraichissement_esg(request, csrd_id):
    csrd = RapportCSRD.objects.get(id=csrd_id)

    context = {"csrd": csrd}

    return render(request, "fragments/esrs.html", context=context)


@login_required
@csrd_required
@require_http_methods(["GET"])
def liste_enjeux_selectionnes(request, csrd_id):
    csrd = RapportCSRD.objects.get(id=csrd_id)

    enjeux_par_esg = {"environnement": {}, "social": {}, "gouvernance": {}}
    for esrs in ESRS:
        enjeux = []
        for enjeu in csrd.enjeux_par_esrs(esrs):
            if enjeu.selection:
                enjeux.append(enjeu)
        if enjeux:
            theme = ThemeESRS[esrs].value
            titre = TitreESRS[esrs].value
            enjeux_par_esg[theme][titre] = enjeux
    context = {"enjeux_par_esg": enjeux_par_esg}

    return render(request, "fragments/liste_enjeux_selectionnes.html", context=context)
