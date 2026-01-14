from functools import wraps

from django.core.exceptions import PermissionDenied

from .enums import UserRole
from .models import Habilitation


def role(*required_roles):
    """
    Décorateur pour vérifier que l'utilisateur a une habilitation pour l'entreprise spécifiée
    et que son rôle satisfait au moins un des rôles requis, en tenant compte de la hiérarchie.
    """

    def decorateur(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # à cette étape, des informations concernant l'utilisateur ont été ajoutées
            # par le middleware `ExtendUserMiddleware`
            user = request.user
            if not user.is_authenticated:
                raise PermissionDenied("L'utilisateur n'est pas authentifié.")

            # la donnée stockée en session est le SIREN de l'entreprise (pas sa PK)
            siren_entreprise = request.session.get("entreprise")
            if not siren_entreprise:
                raise PermissionDenied(
                    "Entreprise manquante pour la vérification des permissions."
                )

            # on évite une dépendance vers Entreprise
            entreprise_courante = None
            for e in user.entreprises:
                if e.siren == siren_entreprise:
                    entreprise_courante = e
                    break

            if not entreprise_courante:
                raise PermissionDenied(
                    "L'utilisateur n'est pas rattaché à l'entreprise courante."
                )

            try:
                habilitation = Habilitation.pour(
                    entreprise=entreprise_courante, utilisateur=user
                )
            except Habilitation.DoesNotExist:
                raise PermissionDenied(
                    "L'utilisateur n'a pas d'habilitation pour l'entreprise courante."
                )

            if habilitation.role and not UserRole.autorise(
                UserRole(habilitation.role), *required_roles
            ):
                raise PermissionDenied("L'utilisateur n'a pas le rôle requis.")

            # Si tout est OK, exécuter la vue originale
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorateur
