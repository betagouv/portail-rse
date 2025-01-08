from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

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
