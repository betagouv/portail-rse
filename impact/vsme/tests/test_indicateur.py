import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from vsme.tests.test_indicateurs import INDICATEURS_VSME_BASE_URL

INDICATEUR_VSME_URL = INDICATEURS_VSME_BASE_URL + "{vsme_id}/indicateur/B1-24-a/"


def test_indicateur_vsme_avec_utilisateur_authentifie(client, alice, rapport_vsme):
    client.force_login(alice)

    url = INDICATEUR_VSME_URL.format(vsme_id=rapport_vsme.id)
    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, f"fragments/indicateur.html")


@pytest.mark.parametrize("indicateur_schema_id", ["ZZZ", "B1-ZZZ"])
def test_indicateur_vsme_inexistant_retourne_une_404(
    indicateur_schema_id, client, alice, rapport_vsme
):
    client.force_login(alice)

    url = (
        INDICATEURS_VSME_BASE_URL
        + f"{rapport_vsme.id}/indicateur/{indicateur_schema_id}/"
    )
    response = client.get(url)

    assert response.status_code == 404


def test_indicateur_vsme_d_un_rapport_inexistant_retourne_une_404(client, alice):
    client.force_login(alice)

    url = INDICATEUR_VSME_URL.format(vsme_id="yolo")
    response = client.get(url)

    assert response.status_code == 404


def test_indicateur_vsme_est_prive(client, bob, rapport_vsme):
    url = INDICATEUR_VSME_URL.format(vsme_id=rapport_vsme.id)
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    # Bob n'est pas rattaché à l'entreprise du rapport VSME
    client.force_login(bob)
    response = client.get(url)

    assert response.status_code == 403
