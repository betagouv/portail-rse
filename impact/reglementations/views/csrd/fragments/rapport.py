from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from habilitations.models import Habilitation
from reglementations.forms.csrd import LienRapportCSRDForm
from reglementations.models.csrd import RapportCSRD


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def selection_rapport(request, csrd_id):
    csrd = get_object_or_404(RapportCSRD, pk=csrd_id)
    request.session["rapport_csrd_courant"] = csrd_id
    return redirect(
        "reglementations:gestion_csrd",
        siren=csrd.entreprise.siren,
        id_etape="introduction",
    )


@login_required
@require_http_methods(["POST"])
def soumettre_lien_rapport(request, csrd_id):
    csrd = get_object_or_404(RapportCSRD, pk=csrd_id)
    role = Habilitation.role_pour(csrd.entreprise, request.user)
    form = LienRapportCSRDForm(instance=csrd, data=request.POST, role=role)
    # les erreurs de format sont captées sur l'input du formulaire coté frontend
    status = 400

    if form.is_valid():
        form.save()
        status = 200

    return render(
        request,
        template_name="fragments/lien_rapport.html",
        status=status,
        context={
            "csrd": csrd,
            "form": form,
        },
    )
