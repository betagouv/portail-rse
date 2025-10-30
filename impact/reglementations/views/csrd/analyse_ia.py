import sentry_sdk
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from analyseia.models import AnalyseIA
from reglementations.models import RapportCSRD


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
