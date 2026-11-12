from django.conf import settings
from django.db.models import Prefetch

from habilitations.models import Habilitation
from users.models import User
from utils.htmx import HttpResponseHXRedirect
from utils.htmx import is_htmx


class ExtendUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # on précharge sur l'utilisateur ses entreprises et ses habilitations
            # car elles sont utilisées presque partout :
            # pour éviter des requêtes supplémentaires
            # dans les vues et les templates
            request.user = User.objects.prefetch_related(
                "entreprise_set",
                Prefetch(
                    "habilitation_set",
                    queryset=Habilitation.objects.select_related("entreprise"),
                ),
            ).get(pk=request.user.pk)

        response = self.get_response(request)

        # rien après

        return response


class HTMXRetargetMiddleware:
    """
    Ajoute un entête `HX-Retarget` à la réponse permettant d'affecter une nouvelle cible de rendu HTMX.
    La nouvelle cible est récupéré via le paramètre de requête `_hx_retarget` si présent.
    Utile lors des redirections ou les modifications d'entêtes ne sont pas préservées.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # uniquement pour les requêtes HTMX et ne doit pas affecter les redirections
        if not is_htmx(request) or (300 <= response.status_code < 400):
            return response

        if new_target := request.GET.get("_hx_retarget"):
            # on applique le changement de cible
            response["HX-Retarget"] = new_target

        return response


class HTMXRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.htmx = request.headers.get("HX-Request") == "true"

        response = self.get_response(request)

        return response


class HTMXAuthRedirectMiddleware:
    """
    Convertit une redirection HTTP vers la page de connexion en réponse `HX-Redirect`
    lorsque la requête est HTMX, pour éviter d'injecter la page de connexion
    dans la cible HTMX (typiquement une modale).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            is_htmx(request)
            and response.status_code == 302
            and response.url.startswith(settings.LOGIN_URL)
        ):
            return HttpResponseHXRedirect(response.url)

        return response
