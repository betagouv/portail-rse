import html
import pytest
from django.urls import reverse

from entreprises.models import Entreprise
from habilitations.models import add_entreprise_to_user, get_habilitation, Habilitation
import api.exceptions


def test_entreprises_page_requires_login(client):
    response = client.get("/entreprises")

    assert response.status_code == 302


def test_entreprises_page_for_logged_user(client, alice):
    entreprise = Entreprise.objects.create(siren="123456789")
    entreprise.users.add(alice)
    client.force_login(alice)

    response = client.get("/entreprises")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page entreprises -->" in content


def test_add_and_attach_to_entreprise(client, mocker, alice):
    client.force_login(alice)
    SIREN = "130025265"
    RAISON_SOCIALE = "ENTREPRISE_TEST"
    data = {"siren": SIREN, "fonctions": "Présidente"}

    mocker.patch(
        "api.recherche_entreprises.recherche",
        return_value={
            "siren": SIREN,
            "effectif": "moyen",
            "raison_sociale": RAISON_SOCIALE,
        },
    )
    response = client.post("/entreprises/add", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises"), 302)]
    content = response.content.decode("utf-8")
    assert "L'entreprise a été ajoutée." in html.unescape(content)

    entreprise = Entreprise.objects.get(siren="130025265")
    assert get_habilitation(entreprise, alice).fonctions == "Présidente"
    assert entreprise.raison_sociale == RAISON_SOCIALE
    assert not entreprise.is_qualified


def test_attach_to_an_existing_entreprise(client, alice, entreprise_factory):
    entreprise = entreprise_factory()
    client.force_login(alice)
    data = {"siren": entreprise.siren, "fonctions": "Présidente"}

    response = client.post("/entreprises/add", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises"), 302)]
    assert entreprise in alice.entreprises
    assert get_habilitation(entreprise, alice).fonctions == "Présidente"


def test_fail_to_add_entreprise(client, alice):
    client.force_login(alice)
    data = {"siren": "", "fonctions": "Présidente"}

    response = client.post("/entreprises/add", data=data, follow=True)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert (
        "Impossible de créer l'entreprise car les données sont incorrectes."
        in html.unescape(content)
    )
    assert Entreprise.objects.count() == 0


def test_fail_to_find_entreprise_in_API(client, mocker, alice):
    client.force_login(alice)
    data = {"siren": "130025265", "fonctions": "Présidente"}

    mocker.patch(
        "api.recherche_entreprises.recherche", side_effect=api.exceptions.APIError
    )
    response = client.post("/entreprises/add", data=data, follow=True)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert (
        "Impossible de créer l'entreprise car le SIREN n'est pas trouvé."
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
    entreprise = Entreprise.objects.create(siren="123456789")
    add_entreprise_to_user(entreprise, alice, "DG")
    return entreprise


def test_detail_entreprise_page(client, alice, unqualified_entreprise):
    client.force_login(alice)

    response = client.get(f"/entreprises/{unqualified_entreprise.siren}")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page details entreprise -->" in content


def test_qualify_entreprise(client, alice, unqualified_entreprise):
    client.force_login(alice)
    data = {
        "raison_sociale": "Entreprise SAS",
        "effectif": "moyen",
        "bdese_accord": True,
    }

    reponse = client.post(f"/entreprises/{unqualified_entreprise.siren}", data=data)

    unqualified_entreprise.refresh_from_db()
    assert unqualified_entreprise.raison_sociale == "Entreprise SAS"
    assert unqualified_entreprise.effectif == "moyen"
    assert unqualified_entreprise.bdese_accord
    assert unqualified_entreprise.is_qualified
