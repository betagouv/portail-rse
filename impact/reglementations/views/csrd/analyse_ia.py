import json

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from openpyxl import Workbook

from reglementations.forms.csrd import DocumentAnalyseIAForm
from reglementations.models import DocumentAnalyseIA
from reglementations.models import RapportCSRD
from reglementations.views.csrd.csrd import _contexte_d_etape
from reglementations.views.csrd.csrd import _xlsx_response
from reglementations.views.csrd.decorators import csrd_required
from reglementations.views.csrd.decorators import document_required


@login_required
@csrd_required
@require_http_methods(["POST"])
def ajout_document(request, csrd_id):
    id_etape = "analyse-ecart"
    csrd = RapportCSRD.objects.get(id=csrd_id)
    data = {**request.POST}
    data["rapport_csrd"] = csrd_id
    form = DocumentAnalyseIAForm(data=data, files=request.FILES)
    if form.is_valid():
        form.save()
        messages.success(request, "Document ajouté")
        return redirect(
            "reglementations:gestion_csrd",
            siren=csrd.entreprise.siren,
            id_etape=id_etape,
        )
    else:
        context = _contexte_d_etape(id_etape, csrd, form)
        template_name = f"reglementations/csrd/etape-{id_etape}.html"
        return render(request, template_name, context, status=400)


@login_required
@document_required
@require_http_methods(["POST"])
def suppression_document(request, id_document):
    document = DocumentAnalyseIA.objects.get(id=id_document)
    document.delete()
    document.fichier.delete(save=False)
    messages.success(request, "Document supprimé")
    id_etape = "analyse-ecart"
    return redirect(
        "reglementations:gestion_csrd",
        siren=document.rapport_csrd.entreprise.siren,
        id_etape=id_etape,
    )


@login_required
@document_required
@require_http_methods(["POST"])
def lancement_analyse_IA(request, id_document):
    document = DocumentAnalyseIA.objects.get(id=id_document)

    if document.etat != "success":
        url = f"{settings.IA_BASE_URL}/run-task"
        response = requests.post(
            url,
            {"document_id": document.id, "url": document.fichier.url},
            headers={"Authorization": f"Bearer {settings.IA_API_TOKEN}"},
        )
        document.etat = response.json()["status"]
        document.save()

    id_etape = "analyse-ecart"
    return redirect(
        "reglementations:gestion_csrd",
        siren=document.rapport_csrd.entreprise.siren,
        id_etape=id_etape,
    )


@csrf_exempt
def etat_analyse_IA(request, id_document):
    try:
        document = DocumentAnalyseIA.objects.get(id=id_document)
    except ObjectDoesNotExist:
        raise Http404("Ce document n'existe pas")

    status = request.POST.get("status")
    document.etat = status
    if message := request.POST.get("msg"):
        document.message = message
    if status == "success":
        document.resultat_json = request.POST["resultat_json"]
    document.save()

    return HttpResponse("OK")


@login_required
@document_required
def resultat_IA_xlsx(request, id_document):
    document = DocumentAnalyseIA.objects.get(id=id_document)

    workbook = Workbook()
    worksheet_trouvees = workbook.active
    worksheet_trouvees.title = "Phrases trouvées"
    worksheet_non_trouvees = workbook.create_sheet("Non trouvées")
    for worksheet in [worksheet_trouvees, worksheet_non_trouvees]:
        worksheet["A1"] = "ESRS"
        worksheet["B1"] = "PAGE"
        worksheet["C1"] = "PHRASE"
    _ajoute_ligne_resultat_ia(workbook, document, False)
    return _xlsx_response(workbook, "resultats.xlsx")


def _ajoute_ligne_resultat_ia(workbook, document, avec_nom_fichier):
    data = json.loads(document.resultat_json)
    for esrs, contenus in data.items():
        for contenu in contenus:
            worksheet = (
                workbook["Non trouvées"]
                if esrs == "Non ESRS"
                else workbook["Phrases trouvées"]
            )
            if avec_nom_fichier:
                ligne = [
                    esrs,
                    document.nom,
                    contenu["PAGES"],
                    contenu["TEXTS"],
                ]
            else:
                ligne = [esrs, contenu["PAGES"], contenu["TEXTS"]]
            worksheet.append(ligne)


@login_required
@csrd_required
def synthese_resultat_IA_xlsx(request, csrd_id):
    csrd = RapportCSRD.objects.get(id=csrd_id)

    workbook = Workbook()
    worksheet_trouvees = workbook.active
    worksheet_trouvees.title = "Phrases trouvées"
    worksheet_non_trouvees = workbook.create_sheet("Non trouvées")
    for worksheet in [worksheet_trouvees, worksheet_non_trouvees]:
        worksheet["A1"] = "ESRS"
        worksheet["B1"] = "FICHIER"
        worksheet["C1"] = "PAGE"
        worksheet["D1"] = "PHRASE"
    for document in csrd.documents_analyses:
        _ajoute_ligne_resultat_ia(workbook, document, True)
    return _xlsx_response(workbook, "synthese_resultats.xlsx")
