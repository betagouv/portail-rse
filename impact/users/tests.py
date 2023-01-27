import pytest
from django.urls import reverse

from entreprises.models import Entreprise, Habilitation
from users.forms import UserCreationForm
from users.models import User


def test_page_creation(client):
    response = client.get("/creation")

    assert response.status_code == 200
    assert "<!-- page creation compte -->" in str(response.content)


@pytest.mark.parametrize("reception_actualites", ["checked", ""])
def test_create_user_with_real_siren(reception_actualites, client, db):
    data = {
        "prenom": "Alice",
        "nom": "User",
        "email": "user@example.com",
        "password1": "Passw0rd!123",
        "password2": "Passw0rd!123",
        "siren": "130025265",  #  Dinum
        "acceptation_cgu": "checked",
        "reception_actualites": reception_actualites,
        "fonctions": "Présidente",
    }

    response = client.post("/creation", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("reglementations"), 302)]

    assert (
        "Votre compte a bien été créé. Vous êtes maintenant connecté."
        in response.content.decode("utf-8")
    )

    user = User.objects.get(email="user@example.com")
    entreprise = Entreprise.objects.get(siren="130025265")
    assert user.created_at
    assert user.updated_at
    assert user.email == "user@example.com"
    assert user.prenom == "Alice"
    assert user.nom == "User"
    assert user.acceptation_cgu == True
    assert user.reception_actualites == (reception_actualites == "checked")
    assert user in entreprise.users.all()
    assert (
        Habilitation.objects.get(user=user, entreprise=entreprise).fonctions
        == "Présidente"
    )


def test_fail_to_create_user_without_cgu(db):
    data = {
        "prenom": "Alice",
        "nom": "User",
        "email": "user@example.com",
        "password1": "Passw0rd!123",
        "password2": "Passw0rd!123",
        "siren": "123456789",
        "acceptation_cgu": "",
        "fonctions": "Présidente",
    }

    bound_form = UserCreationForm(data)

    assert not bound_form.is_valid()
    assert bound_form.errors["acceptation_cgu"] == ["Ce champ est obligatoire."]


def test_fail_to_create_user_with_invalid_siren(db):
    data = {
        "prenom": "Alice",
        "nom": "User",
        "email": "user@example.com",
        "password1": "Passw0rd!123",
        "password2": "Passw0rd!123",
        "siren": "123456abc",
        "acceptation_cgu": "checked",
        "fonctions": "Présidente",
    }

    bound_form = UserCreationForm(data)

    assert not bound_form.is_valid()
    assert bound_form.errors["siren"] == ["Le siren est incorrect"]


def test_fail_to_create_user_with_weak_password(db):
    data = {
        "prenom": "Alice",
        "nom": "User",
        "email": "user@example.com",
        "password1": "password",
        "password2": "password",
        "siren": "123456789",
        "acceptation_cgu": "checked",
        "fonctions": "Présidente",
    }

    bound_form = UserCreationForm(data)

    assert not bound_form.is_valid()
    assert bound_form.errors["password1"] == [
        "Ce mot de passe est trop court. Il doit contenir au minimum 12 caractères.",
        "Ce mot de passe est trop courant.",
        "Le mot de passe doit contenir au moins une minuscule, une majuscule, un chiffre et un caractère spécial",
    ]
