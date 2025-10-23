import json
import logging
from email.message import EmailMessage
from pathlib import Path
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from openpyxl import load_workbook

from .forms import AnalyseIAForm
from .helpers import synthese_analyse
from .models import AnalyseIA
from api import analyse_ia
from api.exceptions import APIError
from entreprises.decorators import entreprise_qualifiee_requise
from reglementations.views import tableau_de_bord_menu_context


logger = logging.getLogger(__name__)


def _contexte_analyses(entreprise):
    context = tableau_de_bord_menu_context(entreprise)
    context |= {
        "form": AnalyseIAForm(),
        "analyses_ia": entreprise.analyses_ia.all(),
        "synthese": synthese_analyse(entreprise),
    }
    return context


@login_required
@entreprise_qualifiee_requise
def analyses(request, entreprise_qualifiee):
    return render(request, "accueil.html", _contexte_analyses(entreprise_qualifiee))


@login_required
@entreprise_qualifiee_requise
@require_http_methods(["POST"])
def ajout_document(request, entreprise_qualifiee):
    data = {**request.POST}
    form = AnalyseIAForm(data=data, files=request.FILES)
    if form.is_valid():
        # les analyses IA étant désormais génériques,
        # on effectue le rattachement à l'entreprise
        form.save()
        entreprise_qualifiee.analyses_ia.add(form.instance)
        messages.success(request, "Document ajouté")
        return redirect("analyseia:analyses", siren=entreprise_qualifiee.siren)
    else:
        return render(
            request,
            "accueil.html",
            _contexte_analyses(entreprise_qualifiee),
            status=400,
        )


@login_required
@require_http_methods(["POST"])
def suppression(request, id_analyse):
    analyse = get_object_or_404(AnalyseIA, pk=id_analyse)
    analyse.delete()
    analyse.fichier.delete(save=False)
    messages.success(request, "Document supprimé")
    return redirect("analyseia:analyses")


@login_required
@require_http_methods(["POST"])
def lancement_analyse(request, id_analyse):
    analyse = get_object_or_404(AnalyseIA, pk=id_analyse)

    if analyse.etat != "success":
        try:
            callback_url = request.build_absolute_uri(
                reverse(
                    "analyseia:etat",
                    kwargs={
                        "id_analyse": analyse.id,
                    },
                )
            )
            etat = analyse_ia.lancement_analyse(
                analyse.id, analyse.fichier.url, callback_url
            )
            analyse.etat = etat
            analyse.save()
            messages.success(
                request,
                "L'analyse a bien été lancée. Celle-ci peut prendre entre quelques secondes et quelques heures. Vous recevrez un email lorsque les résultats seront disponibles.",
            )
        except APIError as exception:
            messages.error(request, exception)

    return redirect("analyseia:analyses")


@login_required
def resultat(request, id_analyse):
    analyse = get_object_or_404(AnalyseIA, pk=id_analyse)
    chemin_xlsx = Path(settings.BASE_DIR, "analyseia/xlsx/template_synthese_ESG.xlsx")
    workbook = load_workbook(chemin_xlsx)
    worksheet = workbook[">>>"]
    worksheet["C14"] = ""
    worksheet = workbook["Phrases relatives aux ESG"]
    _ajoute_ligne_resultat_ia(worksheet, analyse, True, None)
    return xlsx_response(workbook, "resultats.xlsx")


# TODO: externaliser ?


def _ajoute_ligne_resultat_ia(worksheet, document, avec_nom_fichier, contrainte_esrs):
    data = json.loads(document.resultat_json)
    for esrs, contenus in data.items():
        for contenu in contenus:
            if esrs != "Non ESRS" and (
                (not contrainte_esrs) or contrainte_esrs in esrs
            ):
                if avec_nom_fichier:
                    ligne = [
                        "TODO TITRE lIGNE",
                        document.nom,
                        contenu["PAGES"],
                        contenu["TEXTS"],
                    ]
                else:
                    ligne = [
                        "TODO TITRE LIGNE",
                        contenu["PAGES"],
                        contenu["TEXTS"],
                    ]
                worksheet.append(ligne)


def xlsx_response(workbook, filename):
    with NamedTemporaryFile() as tmp:
        workbook.save(tmp.name)
        tmp.seek(0)
        xlsx_stream = tmp.read()

    response = HttpResponse(
        xlsx_stream,
        content_type="application/vnd.openxmlformatsofficedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f"filename={filename}"

    return response


def _envoie_resultat_ia_email(entreprise, resultat_ia_url):
    # FIXME: pull-up / utils
    destinataires = [utilisateur.email for utilisateur in entreprise.users.all()]

    email = EmailMessage(
        to=destinataires,
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    email.template_id = settings.BREVO_RESULTAT_ANALYSE_IA_TEMPLATE

    email.merge_global_data = {
        "resultat_ia_url": resultat_ia_url,
    }
    email.send()


# Fragments / HTMX


@csrf_exempt
def etat(request, id_analyse):
    analyse = get_object_or_404(AnalyseIA, pk=id_analyse)
    status = request.POST.get("status")
    analyse.etat = status
    if message := request.POST.get("msg"):
        analyse.message = message
    if status == "success":
        analyse.resultat_json = request.POST["resultat_json"]
    analyse.save()
    if status in ("success", "error"):
        path = reverse("analyseia:analyses")
        try:
            _envoie_resultat_ia_email(
                request.entreprise,
                f"{request.build_absolute_uri(path)}#onglets",
            )
        except Exception as e:
            logger.exception(e)

    return HttpResponse("OK")


@login_required
def statut_analyse_ia(request, id_analyse):
    analyse = get_object_or_404(AnalyseIA, pk=id_analyse)
    return render(
        request,
        "fragments/statut_analyse.html",
        {
            "analyse": analyse,
        },
    )
