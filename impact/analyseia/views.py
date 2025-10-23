import logging
from datetime import date
from email.message import EmailMessage

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

from .forms import AnalyseIAForm
from .models import AnalyseIA
from api import analyse_ia
from api.exceptions import APIError

logger = logging.getLogger(__name__)


def _contexte_analyses(request):
    return {
        "entreprise": request.entreprise,
        "annee_precedente": date.today().year - 1,
        "form": AnalyseIAForm(),
        "analyses_ia": request.entreprise.analyses_ia.all(),
    }


@login_required
def analyses(request):
    # entreprise = get_object_or_404(Entreprise, siren=request.session.get("entreprise"))
    return render(request, "accueil.html", _contexte_analyses(request))


@login_required
@require_http_methods(["POST"])
def ajout_document(request):
    data = {**request.POST}
    form = AnalyseIAForm(data=data, files=request.FILES)
    if form.is_valid():
        # les analyses IA étant désormais génériques,
        # on effectue le rattachement à l'entreprise
        form.save()
        request.entreprise.analyses_ia.add(form.instance)
        print("entreprise:", request.entreprise)
        print("instance:", form.instance)
        messages.success(request, "Document ajouté")
        return redirect(
            "analyseia:analyses",
        )
    else:
        return render(request, "accueil.html", _contexte_analyses(request), status=400)


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
