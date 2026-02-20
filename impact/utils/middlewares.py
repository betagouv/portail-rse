from django.core.exceptions import ObjectDoesNotExist

from .htmx import is_htmx
from users.models import User


class ExtendUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # en requête plutôt qu'en session :
        # - overhead minime
        # - pas de serialisation nécessaire
        # - utilisation des habilitations omniprésente désormais
        request.habilitations = []
        request.entreprises = []

        if request.user.is_authenticated:
            # on ajoute les habilitations et les entreprises de l'utilisateur
            # pour éviter d'effectuer des requêtes supplementaires
            # dans les vues et les templates
            request.user = User.objects.prefetch_related(
                "entreprise_set", "habilitation_set"
            ).get(pk=request.user.pk)
            # on ajoute des raccourcis vers les habilitations et entreprises de l'utilisateur
            request.habilitations = request.user.habilitation_set.all()
            request.entreprises = request.user.entreprise_set.all()

            if entreprise := request.session.get("entreprise"):
                try:
                    request.entreprise = request.entreprises.get(siren=entreprise)
                except ObjectDoesNotExist:
                    pass

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
