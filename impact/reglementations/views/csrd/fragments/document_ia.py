from django.shortcuts import render

from ..analyse_ia import document_required
from ..analyse_ia import login_required
from analyseia.models import AnalyseIA


@login_required
@document_required
def statut_analyse_ia(request, id_document):
    document = AnalyseIA.objects.get(id=id_document)
    return render(request, "fragments/statut_analyse_ia.html", {"document": document})
