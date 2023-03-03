import html
import pytest
from django.urls import reverse

from entreprises.models import add_entreprise_to_user, Entreprise, Habilitation
from users.forms import UserCreationForm
from users.models import User
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
    assert entreprise.effectif == "moyen"
    assert entreprise.raison_sociale == RAISON_SOCIALE
    assert entreprise in alice.entreprises
    assert (
        Habilitation.objects.get(user=alice, entreprise=entreprise).fonctions
        == "Présidente"
    )


def test_attach_to_an_existing_entreprise(client, alice, entreprise_factory):
    entreprise = entreprise_factory()
    client.force_login(alice)
    data = {"siren": entreprise.siren, "fonctions": "Présidente"}

    response = client.post("/entreprises/add", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises"), 302)]
    assert entreprise in alice.entreprises
    assert (
        Habilitation.objects.get(user=alice, entreprise=entreprise).fonctions
        == "Présidente"
    )


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
