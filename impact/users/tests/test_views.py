import html
from datetime import datetime
from datetime import timezone
from unittest import mock

import pytest
from django.conf import settings
from django.urls import reverse
from freezegun import freeze_time

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from habilitations.models import get_habilitation
from users.models import User
from utils.tokens import make_token
from utils.tokens import uidb64


def test_page_creation(client):
    response = client.get("/creation")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page creation compte -->" in content


@pytest.mark.network
def test_create_user_with_real_siren(client, db, mailoutbox):
    data = {
        "prenom": "Alice",
        "nom": "User",
        "email": "user@domaine.test",
        "password1": "Passw0rd!123",
        "password2": "Passw0rd!123",
        "siren": "130025265",  #  Dinum
        "acceptation_cgu": "checked",
        "reception_actualites": "checked",
        "fonctions": "Présidente",
    }

    response = client.post("/creation", data=data, follow=True)

    assert response.status_code == 200
    reglementation_url = reverse(
        "reglementations:tableau_de_bord", kwargs={"siren": "130025265"}
    )
    assert response.redirect_chain == [
        (reglementation_url, 302),
        (f"{reverse('users:login')}?next={reglementation_url}", 302),
    ]

    assert (
        "Votre compte a bien été créé. Un e-mail de confirmation a été envoyé à user@domaine.test. Confirmez votre adresse e-mail en cliquant sur le lien reçu avant de vous connecter."
        in response.content.decode("utf-8")
    )

    user = User.objects.get(email="user@domaine.test")
    entreprise = Entreprise.objects.get(siren="130025265")
    assert entreprise.denomination == "DIRECTION INTERMINISTERIELLE DU NUMERIQUE"
    assert entreprise.categorie_juridique_sirene == 7120
    assert entreprise.code_pays_etranger_sirene is None
    assert entreprise.code_NAF == "84.11Z"
    assert not CaracteristiquesAnnuelles.objects.filter(entreprise=entreprise)
    assert user.created_at
    assert user.updated_at
    assert user.email == "user@domaine.test"
    assert user.prenom == "Alice"
    assert user.nom == "User"
    assert user.acceptation_cgu == True
    assert user.reception_actualites == True
    assert user.check_password("Passw0rd!123")
    assert user.is_email_confirmed == False
    assert user in entreprise.users.all()
    assert user.uidb64
    assert get_habilitation(user, entreprise).fonctions == "Présidente"
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.from_email == settings.DEFAULT_FROM_EMAIL
    assert list(mail.to) == ["user@domaine.test"]
    assert mail.template_id == settings.SENDINBLUE_CONFIRM_EMAIL_TEMPLATE
    assert mail.merge_global_data == {
        "confirm_email_url": response.wsgi_request.build_absolute_uri(
            reverse(
                "users:confirm_email",
                kwargs={
                    "uidb64": uidb64(user),
                    "token": make_token(user, "confirm_email"),
                },
            )
        )
    }


@pytest.mark.network
def test_create_user_with_invalid_siren(client, db):
    data = {
        "prenom": "Alice",
        "nom": "User",
        "email": "user@domaine.test",
        "password1": "Passw0rd!123",
        "password2": "Passw0rd!123",
        "siren": "000000000",  # Invalid
        "acceptation_cgu": "checked",
        "fonctions": "Présidente",
    }

    response = client.post("/creation", data=data)

    assert response.status_code == 200

    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "L'entreprise n'a pas été trouvée. Vérifiez que le SIREN est correct."
        in content
    )

    assert not User.objects.filter(email="user@domaine.test")
    assert not Entreprise.objects.filter(siren="123456789")


def test_create_user_but_cant_send_confirm_email(
    client, db, mailoutbox, mocker, mock_api_recherche_entreprises
):
    mock_send_confirm_email = mocker.patch(
        "users.views._send_confirm_email", return_value=False
    )

    data = {
        "prenom": "Alice",
        "nom": "User",
        "email": "user@domaine.test",
        "password1": "Passw0rd!123",
        "password2": "Passw0rd!123",
        "siren": "130025265",  #  Dinum
        "acceptation_cgu": "checked",
        "reception_actualites": "",
        "fonctions": "Présidente",
    }

    response = client.post("/creation", data=data, follow=True)

    assert response.status_code == 200
    user = User.objects.get(email="user@domaine.test")
    mock_send_confirm_email.assert_called_once_with(mock.ANY, user)

    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "L'e-mail de confirmation n'a pas pu être envoyé à user@domaine.test. Contactez-nous si cette adresse est légitime."
        in content
    )


def test_confirm_email(client, alice):
    alice.is_email_confirmed = False
    alice.save()
    uid = uidb64(alice)
    token = make_token(alice, "confirm_email")

    url = f"/confirme-email/{uid}/{token}/"
    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("users:login"), 302)]
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Votre adresse e-mail a bien été confirmée. Vous pouvez à présent vous connecter."
        in content
    )

    alice.refresh_from_db()
    assert alice.is_email_confirmed


def test_fail_to_confirm_email_due_to_invalid_token(client, alice):
    alice.is_email_confirmed = False
    alice.save()
    uid = uidb64(alice)

    url = f"/confirme-email/{uid}/invalid-token/"
    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [("/", 302)]
    content = html.unescape(response.content.decode("utf-8"))
    assert "Le lien de confirmation est invalide." in content

    alice.refresh_from_db()
    assert not alice.is_email_confirmed


def test_fail_to_confirm_email_due_to_invalid_user(client, alice):
    alice.is_email_confirmed = False
    alice.save()
    token = make_token(alice, "confirm_email")

    url = f"/confirme-email/invalid-user/{token}/"
    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [("/", 302)]
    content = html.unescape(response.content.decode("utf-8"))
    assert "Le lien de confirmation est invalide." in content

    alice.refresh_from_db()
    assert not alice.is_email_confirmed


def test_account_page_is_not_public(client):
    response = client.get("/mon-compte")

    assert response.status_code == 302


def test_account_page_when_logged_in(client, alice):
    client.force_login(alice)

    response = client.get("/mon-compte")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page mon compte -->" in content, content


@pytest.fixture
def alice_with_password(alice):
    alice.set_password("Passw0rd!123")
    alice.save()  # il faut save après set_password
    return alice


def test_edit_account_info(client, alice_with_password):
    alice = alice_with_password
    client.force_login(alice)

    data = {
        "prenom": "Bob",
        "nom": "Dylan",
        "email": alice.email,
        "reception_actualites": "checked",
        "action": "update-account",
    }

    response = client.post("/mon-compte", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("users:account"), 302)]

    content = response.content.decode("utf-8")
    assert "Votre compte a bien été modifié." in content

    alice.refresh_from_db()
    assert alice.prenom == "Bob"
    assert alice.nom == "Dylan"
    assert alice.reception_actualites
    assert alice.check_password("Passw0rd!123")


def test_edit_email(client, alice_with_password, mailoutbox):
    alice = alice_with_password
    client.force_login(alice)

    data = {
        "prenom": "Bob",
        "nom": "Dylan",
        "email": "bob@domaine.test",
        "reception_actualites": "checked",
        "action": "update-account",
    }

    response = client.post("/mon-compte", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [
        (reverse("users:account"), 302),
        (
            f"{reverse('users:login')}?next=/mon-compte",
            302,
        ),  # l'utilisateur doit se reconnecter
    ]
    assert not response.context["user"].is_authenticated

    content = response.content.decode("utf-8")
    assert (
        "Votre adresse e-mail a bien été modifiée. Un e-mail de confirmation a été envoyé à bob@domaine.test. Confirmez votre adresse e-mail en cliquant sur le lien reçu avant de vous reconnecter."
        in content
    )

    alice.refresh_from_db()
    assert alice.prenom == "Bob"
    assert alice.nom == "Dylan"
    assert alice.email == "bob@domaine.test"
    assert not alice.is_email_confirmed

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.from_email == settings.DEFAULT_FROM_EMAIL
    assert list(mail.to) == ["bob@domaine.test"]
    assert mail.template_id == settings.SENDINBLUE_CONFIRM_EMAIL_TEMPLATE
    assert mail.merge_global_data == {
        "confirm_email_url": response.wsgi_request.build_absolute_uri(
            reverse(
                "users:confirm_email",
                kwargs={
                    "uidb64": uidb64(alice),
                    "token": make_token(alice, "confirm_email"),
                },
            )
        )
    }


def test_edit_password(client, alice):
    client.force_login(alice)

    response = client.get("/mon-compte")

    assert response.status_code == 200

    data = {
        "password1": "Yol0!1234567",
        "password2": "Yol0!1234567",
        "action": "update-password",
    }

    response = client.post("/mon-compte", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [
        (reverse("users:account"), 302),
        (
            f"{reverse('users:login')}?next=/mon-compte",
            302,
        ),  # l'utilisateur doit se reconnecter
    ]

    content = response.content.decode("utf-8")
    assert (
        "Votre mot de passe a bien été modifié. Veuillez vous reconnecter." in content
    )

    alice.refresh_from_db()
    assert alice.check_password("Yol0!1234567")


def test_edit_different_password(client, alice_with_password):
    client.force_login(alice_with_password)

    response = client.get("/mon-compte")

    assert response.status_code == 200

    data = {
        "password1": "Yol0!123456789",
        "password2": "y0Lo?9876543",
        "action": "update-password",
    }

    response = client.post("/mon-compte", data=data, follow=True)

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert "La modification a échoué car le formulaire contient des erreurs." in content

    alice_with_password.refresh_from_db()
    assert alice_with_password.check_password("Passw0rd!123")


def test_update_last_connection_date(client, alice_with_password):
    now = datetime(2023, 1, 27, 16, 1, tzinfo=timezone.utc)
    with freeze_time(now):
        response = client.post(
            "/connexion",
            {"username": "alice@portail-rse.test", "password": "Passw0rd!123"},
            follow=True,
        )

    assert response.status_code == 200
    assert response.context["user"].email == "alice@portail-rse.test"
    alice_with_password.refresh_from_db()
    assert alice_with_password.last_login == now


def test_can_not_login_if_email_is_not_confirmed(client, alice_with_password):
    alice_with_password.is_email_confirmed = False
    alice_with_password.save()

    response = client.post(
        "/connexion",
        {"username": "alice@portail-rse.test", "password": "Passw0rd!123"},
        follow=True,
    )

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert not response.context["user"].is_authenticated
    assert (
        "Merci de confirmer votre adresse e-mail en cliquant sur le lien reçu avant de vous connecter."
        in content
    ), content
