import pytest
from django.urls import reverse

from entreprises.models import Entreprise, Habilitation
from users.forms import UserCreationForm
from users.models import User


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


def test_add_and_attach_to_entreprise(client, alice):
    client.force_login(alice)
    data = {"siren": "130025265"}

    response = client.post("/entreprises/add", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises"), 302)]
    entreprise = Entreprise.objects.get(siren="130025265")
    assert entreprise in alice.entreprises


def test_attach_to_an_existing_entreprise(client, alice, entreprise_factory):
    entreprise = entreprise_factory()
    client.force_login(alice)
    data = {"siren": entreprise.siren}

    response = client.post("/entreprises/add", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises"), 302)]
    assert entreprise in alice.entreprises