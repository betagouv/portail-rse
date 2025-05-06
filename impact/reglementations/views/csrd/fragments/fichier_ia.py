from django.shortcuts import render

from ..analyse_ia import document_required
from ..analyse_ia import login_required
from reglementations.models import DocumentAnalyseIA


@login_required
@document_required
def statut_analyse_ia(request, id_document):
    document = DocumentAnalyseIA.objects.get(id=id_document)
    return render(request, "fragments/statut_analyse_ia.html", {"document": document})
