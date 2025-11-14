from django.urls import reverse

from habilitations.models import Habilitation


INDEX_URL = "/tableau-de-bord/{siren}/reglementations/index/"


def test_index_est_prive(client, entreprise_factory, alice):
    entreprise = entreprise_factory()

    url = INDEX_URL.format(siren=entreprise.siren)
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    client.force_login(alice)
    response = client.get(url)

    assert response.status_code == 403


def test_index_avec_utilisateur_authentifie(client, entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    url = INDEX_URL.format(siren=entreprise.siren)
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["entreprise"] == entreprise


def test_index_accessible_avec_entreprise_non_qualifiee(
    client, entreprise_non_qualifiee, alice
):
    Habilitation.ajouter(entreprise_non_qualifiee, alice, fonctions="Présidente")
    client.force_login(alice)

    url = INDEX_URL.format(siren=entreprise_non_qualifiee.siren)
    response = client.get(url)

    assert response.status_code == 200


def test_index_avec_entreprise_inexistante(client, alice):
    client.force_login(alice)

    url = INDEX_URL.format(siren="yolo")
    response = client.get(url)

    assert response.status_code == 404
