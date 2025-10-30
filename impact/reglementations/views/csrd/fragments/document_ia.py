from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from ..decorators import document_required
from analyseia.models import AnalyseIA
from reglementations.models.csrd import RapportCSRD


@login_required
@document_required
def statut_analyse_ia(request, id_document, csrd_id):
    document = AnalyseIA.objects.get(id=id_document)
    rapport_csrd = get_object_or_404(RapportCSRD, pk=csrd_id)
    return render(
        request,
        "fragments/statut_analyse_ia.html",
        {
            "document": document,
            "csrd": rapport_csrd,
        },
    )
