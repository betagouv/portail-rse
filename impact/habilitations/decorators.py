from functools import wraps

from django.http import HttpResponseForbidden

from .enums import UserRole
from .models import Habilitation


def role(*required_roles):
    """
    Décorateur pour vérifier que l'utilisateur authentifié a une habilitation
    pour l'entreprise spécifiée et que son rôle satisfait au moins un des rôles requis,
    en tenant compte de la hiérarchie.
    """

    def decorateur(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return HttpResponseForbidden("L'utilisateur n'est pas authentifié.")

            entreprise = request.session.get("entreprise")
            if not entreprise:
                return HttpResponseForbidden(
                    "Paramètre Entreprise manquant pour la vérification des permissions."
                )

            try:
                habilitation = Habilitation.pour(
                    entreprise=entreprise, utilisateur=user
                )
            except Habilitation.DoesNotExist:
                return HttpResponseForbidden(
                    "L'utilisateur n'a pas d'habilitation pour l'entreprise."
                )

            if not UserRole.autorise(habilitation.role, *required_roles):
                return HttpResponseForbidden("L'utilisateur n'a pas le rôle requis.")

            # Si tout est OK, exécuter la vue originale
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorateur
