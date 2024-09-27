"""
Fragments HTMX pour la sélection des enjeux par ESRS
"""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from reglementations.forms.csrd import EnjeuxRapportCSRDForm
from reglementations.models.csrd import RapportCSRD

"""
Vues de fragments HTMX :
    Optimisation du format et de la taille des réponses.
"""


@login_required
@require_http_methods(["GET", "POST"])
def selection_enjeux(request, csrd_id, esrs):
    csrd = get_object_or_404(RapportCSRD, id=csrd_id)

    if not csrd.modifiable_par(request.user):
        raise PermissionDenied(
            "L'utilisateur n'a pas les permissions nécessaires pour accéder à ce rapport CSRD"
        )

    if request.method == "GET":
        return render(
            request,
            template_name="fragments/selection_enjeux.html",
            context={"form": EnjeuxRapportCSRDForm(instance=csrd, esrs=esrs)},
        )

    # Dans un fragment, l'utilisation du Post/Redirect/Get n'est pas nécessaire (XHR)
    form = EnjeuxRapportCSRDForm(request.POST, instance=csrd, esrs=esrs)

    if form.is_valid():
        form.save()

    return render(
        request,
        "fragments/esrs.html",
        context={"csrd": csrd},
    )
