from django.urls import reverse

from habilitations.models import Habilitation


INDEX_URL = "/tableau-de-bord/{id_public}/reglementations/index/"


def test_index_avec_utilisateur_authentifie_redirige_vers_le_tableau_de_bord(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    url = INDEX_URL.format(id_public=entreprise.id_public)
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse(
        "reglementations:tableau_de_bord",
        kwargs={
            "id_public": entreprise.id_public,
        },
    )


def test_index_accessible_avec_entreprise_non_qualifiee_redirige_vers_le_tableau_de_bord(
    client, entreprise_non_qualifiee, alice
):
    # le fait d'être qualifié ou non sera traité dans la page d'arrivée
    Habilitation.ajouter(entreprise_non_qualifiee, alice, fonctions="Présidente")
    client.force_login(alice)

    url = INDEX_URL.format(id_public=entreprise_non_qualifiee.id_public)
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse(
        "reglementations:tableau_de_bord",
        kwargs={
            "id_public": entreprise_non_qualifiee.id_public,
        },
    )


def test_index_avec_entreprise_inexistante(client, alice):
    client.force_login(alice)

    url = INDEX_URL.format(id_public="00000000-0000-0000-0000-000000000000")
    response = client.get(url)

    assert response.status_code == 404
