from django.urls import reverse

from entreprises.models import Entreprise
from users.models import User


def test_page_creation(client):
    response = client.get("/creation")

    assert response.status_code == 200
    assert "<!-- page creation compte -->" in str(response.content)


def test_create_user(client, db):
    data = {
        "email": "user@example.com",
        "password1": "password",
        "password2": "password",
    }
    response = client.post("/creation", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("reglementations"), 302)]

    user = User.objects.get(email="user@example.com")
    assert user


def test_create_user_with_entreprise(client, db):
    data = {
        "email": "user@example.com",
        "password1": "password",
        "password2": "password",
        "siren": "123456789",
    }

    response = client.post("/creation", data=data, follow=True)

    user = User.objects.get(email="user@example.com")
    entreprise = Entreprise.objects.get(siren="123456789")

    assert user in entreprise.users.all()
