import sentry_sdk
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from analyseia.models import AnalyseIA
from api import analyse_ia
from api.exceptions import APIError
from reglementations.forms.csrd import DocumentAnalyseIAForm
from reglementations.models import RapportCSRD
from reglementations.views.csrd.csrd import contexte_d_etape
from reglementations.views.csrd.decorators import csrd_required
from reglementations.views.csrd.decorators import document_required


@login_required
@csrd_required
@require_http_methods(["POST"])
def ajout_document(request, csrd_id):
    id_etape = "analyse-ecart"
    csrd = RapportCSRD.objects.get(id=csrd_id)
    data = {**request.POST}
    # data["rapport_csrd"] = csrd_id
    form = DocumentAnalyseIAForm(data=data, files=request.FILES)
    if form.is_valid():
        # les analyses IA étant désormais génériques,
        # on effectue le rattachement au rapport CSRD
        form.save()
        form.instance.rapports_csrd.add(csrd)
        messages.success(request, "Document ajouté")
        return redirect(
            "reglementations:gestion_csrd",
            siren=csrd.entreprise.siren,
            id_etape=id_etape,
        )
    else:
        context = contexte_d_etape(id_etape, csrd, form)
        template_name = f"reglementations/csrd/etape-{id_etape}.html"
        return render(request, template_name, context, status=400)


@login_required
@document_required
@require_http_methods(["POST"])
def lancement_analyse_IA(request, id_document, csrd_id):
    document = AnalyseIA.objects.get(id=id_document)
    rapport_csrd = get_object_or_404(RapportCSRD, pk=csrd_id)

    if document.etat != "success":
        try:
            callback_url = request.build_absolute_uri(
                reverse(
                    "reglementations:etat_analyse_IA",
                    kwargs={
                        "id_document": document.id,
                        "csrd_id": rapport_csrd.id,
                    },
                )
            )
            etat = analyse_ia.lancement_analyse(
                document.id, document.fichier.url, callback_url
            )
            document.etat = etat
            document.save()
            messages.success(
                request,
                "L'analyse a bien été lancée. Celle-ci peut prendre entre quelques secondes et quelques heures. Vous recevrez un email lorsque les résultats seront disponibles.",
            )
        except APIError as exception:
            messages.error(request, exception)

    id_etape = "analyse-ecart"
    return redirect(
        "reglementations:gestion_csrd",
        siren=rapport_csrd.entreprise.siren,
        id_etape=id_etape,
    )


@csrf_exempt
def etat_analyse_IA(request, id_document, csrd_id):
    try:
        document = AnalyseIA.objects.get(id=id_document)
    except ObjectDoesNotExist:
        raise Http404("Ce document n'existe pas")

    rapport_csrd = get_object_or_404(RapportCSRD, pk=csrd_id)

    status = request.POST.get("status")
    document.etat = status
    if message := request.POST.get("msg"):
        document.message = message
    if status == "success":
        document.resultat_json = request.POST["resultat_json"]
    document.save()
    if status in ("success", "error"):
        path = reverse(
            "reglementations:gestion_csrd",
            kwargs={
                "siren": rapport_csrd.entreprise.siren,
                "id_etape": "analyse-ecart",
            },
        )
        try:
            envoie_resultat_ia_email(
                document, rapport_csrd, f"{request.build_absolute_uri(path)}#onglets"
            )
        except Exception as e:
            with sentry_sdk.new_scope() as scope:
                scope.set_level("info")
                sentry_sdk.capture_exception(e)

    return HttpResponse("OK")


# FIXME : rapport CSRD
def envoie_resultat_ia_email(document, rapport_csrd, resultat_ia_url):
    destinataires = [
        utilisateur.email for utilisateur in rapport_csrd.entreprise.users.all()
    ]

    email = EmailMessage(
        to=destinataires,
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    email.template_id = settings.BREVO_RESULTAT_ANALYSE_IA_TEMPLATE

    email.merge_global_data = {
        "resultat_ia_url": resultat_ia_url,
    }
    email.send()
