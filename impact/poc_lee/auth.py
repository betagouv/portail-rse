import hmac
from functools import wraps

from django.conf import settings
from django.http import Http404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def token_lee_requis(function):
    @csrf_exempt
    @wraps(function)
    def wrap(request, *args, **kwargs):
        attendu = settings.POC_LEE_TOKEN
        if not attendu:
            raise Http404()
        entete = request.headers.get("Authorization", "")
        recu = entete.removeprefix("Bearer ") if entete.startswith("Bearer ") else ""
        if not hmac.compare_digest(recu.encode(), attendu.encode()):
            return JsonResponse({"erreur": "token-invalide"}, status=401)
        return function(request, *args, **kwargs)

    return wrap
