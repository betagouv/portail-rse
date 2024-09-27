from users.models import User


class ExtendUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # on ajoute les habilitations et les entreprises de l'utilisateur
            # pour éviter d'effectuer des requêtes supplementaires
            # dans les vues et les templates
            request.user = User.objects.prefetch_related(
                "entreprise_set", "habilitation_set"
            ).get(pk=request.user.pk)

        response = self.get_response(request)

        # rien après

        return response
