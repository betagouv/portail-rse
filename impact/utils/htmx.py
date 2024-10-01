"""
Utilitaires divers pour HTMX
"""
from django.utils.http import urlencode


def is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def retarget_params(request, new_target) -> str:
    # permet de rediriger la cible d'une requête HTMX
    # en passant la nouvelle cible en paramètre de requête
    if is_htmx(request) and new_target:
        return urlencode({"_hx_retarget": new_target})
