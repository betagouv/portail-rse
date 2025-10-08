from .backends import CustomOIDCAuthenticationBackend


class OIDCMiddleware:
    """Permet de stocker certains `claims` OIDC en session juste après une connexion ProConnect"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # le token d'accès n'est pas valable très longtemps,
        # mais suffisament pour récupérer les informations
        # intéressantes de ProConnect et les stocker en session
        if access_token := request.session.get("oidc_access_token"):
            if not request.session.get("oidc_user_claims"):
                # on récupère les claims OIDC, essentiellement pour le SIRET
                # plus simple de refaire un appel à `user_info` que de tordre
                # le backend pour effectuer des modifications de session
                # (ce qui n'est pas son rôle)
                backend = CustomOIDCAuthenticationBackend()
                user_info = backend.get_userinfo(access_token, None, None)
                request.session["oidc_user_claims"] = {
                    "sub": user_info["sub"],
                    "siren": user_info["siret"][:9],
                }
                # le token d'accès ne devrait plus être utilisé
                request.session.pop("oidc_access_token")
                request.session.save()

        response = self.get_response(request)

        return response
