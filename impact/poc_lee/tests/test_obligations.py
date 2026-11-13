from unittest.mock import ANY

from poc_lee.tests.conftest import JETON
from reglementations.views.toutes_reglementations import REGLEMENTATIONS

URL = "/poc-lee/entreprises/{siren}/obligations"


def lit_les_obligations(client, siren="095680393", jeton=JETON):
    headers = {"HTTP_AUTHORIZATION": f"Bearer {jeton}"} if jeton else {}
    return client.get(URL.format(siren=siren), **headers)


def test_renvoie_les_obligations_calculees_par_le_portail(
    client, poc_actif, sans_reseau, pme_transport
):
    response = lit_les_obligations(client)

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "siren": "095680393",
        "denomination": "Entreprise SAS",
        "obligations": ANY,
    }
    assert len(body["obligations"]) == len(REGLEMENTATIONS)
    assert {
        "id": "index-egalite-professionnelle",
        "titre": "Index de l’égalité professionnelle",
        "statut": "a-actualiser",
        "detail": ANY,
        "url": "https://portail-rse.beta.gouv.fr/fiches-reglementaires/index-egalite-professionnelle/",
    } in body["obligations"]


def test_n_appelle_aucune_api_externe(client, poc_actif, sans_reseau, pme_transport):
    response = lit_les_obligations(client)

    assert response.status_code == 200


def test_refuse_un_jeton_invalide(client, poc_actif, pme_transport):
    response = lit_les_obligations(client, jeton="faux")

    assert response.status_code == 401
    assert response.json() == {"erreur": "token-invalide"}


def test_refuse_une_requete_sans_jeton(client, poc_actif, pme_transport):
    response = lit_les_obligations(client, jeton=None)

    assert response.status_code == 401
    assert response.json() == {"erreur": "token-invalide"}


def test_repond_404_quand_le_poc_est_desactive(client, settings, pme_transport):
    settings.POC_LEE_TOKEN = ""

    response = lit_les_obligations(client)

    assert response.status_code == 404


def test_repond_404_pour_une_entreprise_inconnue(client, poc_actif, db):
    response = lit_les_obligations(client, siren="999999999")

    assert response.status_code == 404
    assert response.json() == {"erreur": "entreprise-inconnue"}


def test_repond_404_pour_une_entreprise_non_qualifiee(
    client, poc_actif, entreprise_non_qualifiee
):
    entreprise_non_qualifiee.identifiant = "095680393"
    entreprise_non_qualifiee.save()

    response = lit_les_obligations(client)

    assert response.status_code == 404
    assert response.json() == {"erreur": "entreprise-non-qualifiee"}


def test_refuse_une_entreprise_hors_demo(client, poc_actif, entreprise_factory):
    entreprise_factory(identifiant="000000001")

    response = lit_les_obligations(client, siren="000000001")

    assert response.status_code == 404
    assert response.json() == {"erreur": "entreprise-inconnue"}


def test_repond_404_hors_mode_debug(client, poc_actif, settings, pme_transport):
    settings.DEBUG = False

    response = lit_les_obligations(client)

    assert response.status_code == 404
