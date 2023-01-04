from django.urls import reverse

from entreprises.models import Entreprise
from users.models import User


def test_page_creation(client):
    response = client.get("/creation")

    assert response.status_code == 200
    assert "<!-- page creation compte -->" in str(response.content)


def test_create_user_with_real_siren(client, db):
    data = {
        "email": "user@example.com",
        "password1": "password",
        "password2": "password",
        "siren": "130025265",  #  Dinum
    }

    response = client.post("/creation", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("reglementations"), 302)]

    user = User.objects.get(email="user@example.com")
    entreprise = Entreprise.objects.get(siren="130025265")
    assert user.email == "user@example.com"
    assert user in entreprise.users.all()


def test_create_user_with_invalid_siren(client, db):
    data = {
        "email": "user@example.com",
        "password1": "password",
        "password2": "password",
        "siren": "123456abc",
    }

    response = client.post("/creation", data=data, follow=True)

    assert User.objects.count() == 0
    assert Entreprise.objects.count() == 0
