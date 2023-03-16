import html
import pytest
from django.urls import reverse

import api.exceptions
from api.tests.fixtures import mock_api_recherche_entreprise
from entreprises.models import Entreprise
from habilitations.models import add_entreprise_to_user, get_habilitation, Habilitation


def test_entreprises_page_requires_login(client):
    response = client.get("/entreprises")

    assert response.status_code == 302


def test_entreprises_page_for_logged_user(client, alice):
    entreprise = Entreprise.objects.create(siren="00000001")
    entreprise.users.add(alice)
    client.force_login(alice)

    response = client.get("/entreprises")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page entreprises -->" in content


def test_add_and_attach_to_entreprise(client, alice, mock_api_recherche_entreprise):
    client.force_login(alice)
    data = {"siren": "000000001", "fonctions": "Présidente"}

    response = client.post("/entreprises/add", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises:entreprises"), 302)]

    content = response.content.decode("utf-8")
    assert "L'entreprise a été ajoutée." in html.unescape(content)

    entreprise = Entreprise.objects.get(siren="000000001")
    assert get_habilitation(entreprise, alice).fonctions == "Présidente"
    assert entreprise.raison_sociale == "Entreprise SAS"
    assert not entreprise.is_qualified


def test_attach_to_an_existing_entreprise(client, alice, entreprise_factory):
    entreprise = entreprise_factory()
    client.force_login(alice)
    data = {"siren": entreprise.siren, "fonctions": "Présidente"}

    response = client.post("/entreprises/add", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises:entreprises"), 302)]
    assert entreprise in alice.entreprises
    assert get_habilitation(entreprise, alice).fonctions == "Présidente"


def test_fail_to_add_entreprise(client, alice):
    client.force_login(alice)
    data = {"siren": "unvalid", "fonctions": "Présidente"}

    response = client.post("/entreprises/add", data=data, follow=True)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert (
        "Impossible de créer l'entreprise car les données sont incorrectes."
        in html.unescape(content)
    )
    assert Entreprise.objects.count() == 0


def test_fail_to_find_entreprise_in_API(client, alice, mock_api_recherche_entreprise):
    client.force_login(alice)
    mock_api_recherche_entreprise.side_effect = api.exceptions.APIError(
        "L'entreprise n'a pas été trouvée. Vérifiez que le SIREN est correct."
    )
    data = {"siren": "000000001", "fonctions": "Présidente"}

    response = client.post("/entreprises/add", data=data, follow=True)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert (
        "L'entreprise n'a pas été trouvée. Vérifiez que le SIREN est correct."
        in html.unescape(content)
    )
    assert Entreprise.objects.count() == 0


def test_fail_because_already_existing_habilitation(client, alice, entreprise_factory):
    entreprise = entreprise_factory()
    add_entreprise_to_user(entreprise, alice, "DG")
    client.force_login(alice)
    data = {"siren": entreprise.siren, "fonctions": "Présidente"}

    response = client.post("/entreprises/add", data=data, follow=True)

    assert Habilitation.objects.count() == 1
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert (
        "Impossible d'ajouter cette entreprise. Vous y êtes déjà rattaché·e."
        in html.unescape(content)
    )


@pytest.fixture
def unqualified_entreprise(alice):
    entreprise = Entreprise.objects.create(siren="00000001")
    return entreprise


def test_qualification_page_is_not_public(client, alice, unqualified_entreprise):
    url = f"/entreprises/{unqualified_entreprise.siren}"
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("login")
    assert response.url == f"{connexion_url}?next={url}"

    client.force_login(alice)
    response = client.get(url)

    assert response.status_code == 403


def test_qualification_page(
    client, alice, unqualified_entreprise, mock_api_recherche_entreprise
):
    add_entreprise_to_user(unqualified_entreprise, alice, "Présidente")
    client.force_login(alice)

    response = client.get(f"/entreprises/{unqualified_entreprise.siren}")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page qualification entreprise -->" in content
    mock_api_recherche_entreprise.assert_called_once_with(unqualified_entreprise.siren)

    unqualified_entreprise.refresh_from_db()
    assert unqualified_entreprise.raison_sociale == "Entreprise SAS"
    assert not unqualified_entreprise.is_qualified


def test_qualify_entreprise(
    client, alice, unqualified_entreprise, mock_api_recherche_entreprise
):
    add_entreprise_to_user(unqualified_entreprise, alice, "Présidente")
    client.force_login(alice)
    data = {
        "effectif": "moyen",
        "bdese_accord": True,
    }

    url = f"/entreprises/{unqualified_entreprise.siren}"
    response = client.get(url)
    response = client.post(url, data=data)

    unqualified_entreprise.refresh_from_db()
    assert unqualified_entreprise.raison_sociale == "Entreprise SAS"
    assert unqualified_entreprise.effectif == "moyen"
    assert unqualified_entreprise.bdese_accord
    assert unqualified_entreprise.is_qualified


def test_qualify_entreprise_error(
    client, alice, unqualified_entreprise, mock_api_recherche_entreprise
):
    add_entreprise_to_user(unqualified_entreprise, alice, "Présidente")
    client.force_login(alice)
    data = {
        "effectif": "yolo",
        "bdese_accord": True,
    }

    url = f"/entreprises/{unqualified_entreprise.siren}"
    response = client.get(url)
    response = client.post(url, data=data)

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "L'entreprise n'a pas été enregistrée car le formulaire contient des erreurs"
        in content
    )

    unqualified_entreprise.refresh_from_db()
    assert not unqualified_entreprise.is_qualified
