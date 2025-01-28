from typing import OrderedDict

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from reglementations.enums import ThemeESRS
from reglementations.enums import TitreESRS
from reglementations.forms.csrd import EnjeuxMaterielsRapportCSRDForm
from reglementations.models.csrd import RapportCSRD
from reglementations.views.fragments.decorators import csrd_required


def _grouper_enjeux_par_esrs(enjeux):
    # plus facile ici que :
    # - dans le template
    # - en une seule requête SQL
    resultat = []
    lst = enjeux.order_by("esrs")
    parts = OrderedDict(
        sorted(
            {
                k: [d for d in lst if d.esrs == k] for k in set(d.esrs for d in lst)
            }.items()
        )
    )
    for esrs, enjeux_ in parts.items():
        resultat.append(
            {
                "titre": TitreESRS[esrs].value,
                "esrs": esrs,
                "analyses": len(enjeux.analyses().filter(esrs=esrs)),
                "a_analyser": len(enjeux_),
                "enjeux": enjeux_,
                "nb_materiels": len(enjeux.materiels().filter(esrs=esrs)),
            }
        )

    return resultat


@login_required
@csrd_required
@require_http_methods(["GET"])
def rafraichissement_enjeux_materiels(request, csrd_id):
    csrd = get_object_or_404(RapportCSRD, id=csrd_id)
    enjeux_selectionnes = csrd.enjeux.selectionnes()
    enjeux_non_analyses = csrd.enjeux.non_analyses()

    context = {
        "csrd": csrd,
        "enjeux_environnement": _grouper_enjeux_par_esrs(
            enjeux_selectionnes.environnement()
        ),
        "enjeux_social": _grouper_enjeux_par_esrs(enjeux_selectionnes.social()),
        "enjeux_gouvernance": _grouper_enjeux_par_esrs(
            enjeux_selectionnes.gouvernance()
        ),
        "can_download": enjeux_selectionnes.count() != enjeux_non_analyses.count(),
        "nb_enjeux_non_analyses": enjeux_non_analyses.count(),
    }

    return render(request, "fragments/esrs_materiels.html", context)


@login_required
@csrd_required
@require_http_methods(["GET", "POST"])
def selection_enjeux_materiels(request, csrd_id, esrs):
    csrd = get_object_or_404(RapportCSRD, id=csrd_id)
    qs = csrd.enjeux.filter(esrs=esrs).selectionnes()
    template_name = "fragments/selection_enjeux_materiels.html"
    context = {
        "csrd": csrd,
        "esrs": esrs,
        "theme": ThemeESRS[esrs].value,
        "titre": TitreESRS[esrs].value,
    }

    if request.method == "GET":
        return render(
            request,
            template_name=template_name,
            context=context | {"form": EnjeuxMaterielsRapportCSRDForm(qs=qs)},
        )

    form = EnjeuxMaterielsRapportCSRDForm(request.POST, qs=qs)

    if form.is_valid() and not csrd.bloque:
        form.save()

    response = render(
        request,
        template_name=template_name,
        context=context | {"form": form},
    )
    response.headers["HX-Trigger"] = "formValidated"

    return response


@login_required
@csrd_required
@require_http_methods(["GET"])
def liste_enjeux_materiels(request, csrd_id):
    csrd = get_object_or_404(RapportCSRD, id=csrd_id)
    enjeux_materiels_selectionnes = csrd.enjeux.selectionnes()
    context = {
        "csrd": csrd,
        "enjeux_environnement": _grouper_enjeux_par_esrs(
            enjeux_materiels_selectionnes.environnement()
        ),
        "enjeux_social": _grouper_enjeux_par_esrs(
            enjeux_materiels_selectionnes.social()
        ),
        "enjeux_gouvernance": _grouper_enjeux_par_esrs(
            enjeux_materiels_selectionnes.gouvernance()
        ),
    }

    return render(request, "fragments/liste_enjeux_materiels.html", context)
