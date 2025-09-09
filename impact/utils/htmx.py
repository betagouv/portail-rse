"""
Utilitaires divers pour HTMX
"""

from django.http import HttpResponse
from django.http.response import HttpResponseRedirectBase
from django.utils.http import urlencode


def is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def retarget_params(request, new_target) -> str:
    # permet de rediriger la cible d'une requête HTMX
    # en passant la nouvelle cible en paramètre de requête
    if is_htmx(request) and new_target:
        return urlencode({"_hx_retarget": new_target})


class HttpResponseRedirectSeeOther(HttpResponseRedirectBase):
    # Assez surpris de voir tous les autres redirects implémentés en Django
    # mais pas celui-ci.
    # Pourtant pour faire l'équivalent d'un Post-Redirect-Get avec d'autres méthodes,
    # ce type de redirection est obligatoire si la requête initiale et celle de redirection
    # ont des méthodes HTTP différentes.
    # Par exemple, DELETE puis redirect avec un GET est impossible avec une 302
    # C'est par exemple très utile avec HTMX pour utiliser autre chose que des GET et des POST.
    status_code = 303

class HttpResponseHXRedirect(HttpResponse):
    # Ajoute un entête `HX-Redirect` à la réponse permettant de déclencher une redirection.
    # L'url cible est récupérée via l'argument redirect_to
    # https://htmx.org/headers/hx-redirect/
    def __init__(self, redirect_to, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["HX-Redirect"] = redirect_to
