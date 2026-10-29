from oidc.backends import CustomOIDCAuthenticationBackend


def test_retire_les_balises_html_du_prenom_et_du_nom():
    user_info = {
        "given_name": "<script>Alice</script>",
        "usual_name": "<b>User</b>",
        "siret": "12345678900012",
        "sub": "sub-id",
    }

    claims = CustomOIDCAuthenticationBackend().get_extra_claims(user_info)

    assert claims["prenom"] == "scriptAlice/script"
    assert claims["nom"] == "bUser/b"
