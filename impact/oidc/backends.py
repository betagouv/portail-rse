from lasuite.oidc_login.backends import OIDCAuthenticationBackend


class CustomOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    # Pour optimiser la connexion ProConnect dans le contexte du Portail RSE

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
