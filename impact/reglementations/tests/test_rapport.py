from django.urls import reverse

from habilitations.models import Habilitation


RAPPORT_URL = "/tableau-de-bord/{siren}/rapport/"
RAPPORT_URL_GENERIQUE = "/tableau-de-bord/rapport/"


def test_page_intermediaire_de_rapport_avec_utilisateur_authentifie_redirige_vers_le_tableau_de_bord(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    url = RAPPORT_URL.format(siren=entreprise.siren)
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse(
        "reglementations:tableau_de_bord",
        kwargs={
            "siren": entreprise.siren,
        },
    )


def test_page_intermediaire_de_rapport_avec_entreprise_non_qualifiee_redirige_vers_le_tableau_de_bord(
    client, entreprise_non_qualifiee, alice
):
    # le fait d'être qualifié ou non sera traité dans la page d'arrivée
    Habilitation.ajouter(entreprise_non_qualifiee, alice, fonctions="Présidente")
    client.force_login(alice)

    url = RAPPORT_URL.format(siren=entreprise_non_qualifiee.siren)
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse(
        "reglementations:tableau_de_bord",
        kwargs={
            "siren": entreprise_non_qualifiee.siren,
        },
    )


def test_page_de_rapport_generique_redirige_vers_le_tableau_de_bord_generique(
    client, entreprise_non_qualifiee, alice
):
    response = client.get(RAPPORT_URL_GENERIQUE)

    assert response.status_code == 302
    assert response.url == reverse(
        "reglementations:tableau_de_bord",
    )
