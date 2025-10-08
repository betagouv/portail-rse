from django.core.exceptions import SuspiciousOperation
from lasuite.oidc_login.backends import OIDCAuthenticationBackend


class CustomOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    # Pour optimiser la connexion ProConnect dans le contexte du Portail RSE

    def get_extra_claims(self, user_info):
        return {
            "prenom": user_info["given_name"],
            "nom": user_info["usual_name"],
            "siret": user_info["siret"],
            # le claim `sub` est nommé `oidc_sub_id` dans le modèle pour être plus explicite
            "oidc_sub_id": user_info["sub"],
        }

    def create_user(self, claims):
        sub = claims.get(self.OIDC_USER_SUB_FIELD)
        if sub is None:
            raise SuspiciousOperation(
                "Claims contained no recognizable user identification"
            )

        # le SIRET des claims n'est pas directement mappé sur le modèle user
        del claims["siret"]

        # on considère qu'un utilisateur identifié par ProConnect a un e-mail valide
        user = self.UserModel(is_email_confirmed=True, **claims)
        user.set_unusable_password()
        user.save()

        # TODO: log me

        return user

    def update_user_if_needed(self, user, claims):
        updated_claims = {}
        for key in claims:
            if not hasattr(user, key):
                continue

            claim_value = claims.get(key)
            if claim_value and claim_value != getattr(user, key):
                updated_claims[key] = claim_value

        if updated_claims:
            # il y a un problème dans la version initiale :
            # si on part d'un pool d'utilisateurs qui n'a jamais été connecté à ProConnect
            # toute la base est mise à jour avec le `sub` actuel (c'est mal)
            # TODO: investiguer plus avant, voir si à remonter à la suite
            self.UserModel.objects.filter(pk=user.pk).update(**updated_claims)
