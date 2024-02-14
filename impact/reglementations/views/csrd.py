from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy

from reglementations.views.base import Reglementation


class CSRDReglementation(Reglementation):
    title = "Rapport de durabilité - Directive CSRD"
    more_info_url = reverse_lazy("reglementations:fiche_csrd")
    tag = "tag-durabilite"
    summary = "Publier un rapport de durabilité"


@login_required
def csrd(request):
    return render(
        request,
        "reglementations/espace-csrd.html",
    )
