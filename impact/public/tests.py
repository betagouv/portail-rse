import html

import pytest
from django.urls import reverse

import api.exceptions
from entreprises.models import CaracteristiquesAnnuelles


def test_page_index_pour_un_visiteur_anonyme(client):
    response = client.get("/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page index -->" in content


def test_redirection_de_la_page_index_vers_ses_reglementations_si_l_utilisateur_est_connecte(
    client, alice
):
    client.force_login(alice)

    response = client.get("/", follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [
        (reverse("reglementations:reglementations"), 302),
    ]


def test_page_simulation(client):
    response = client.get("/simulation")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page simulation -->" in content


def test_page_contact(client):
    response = client.get("/contact")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page contact -->" in content


@pytest.mark.parametrize(
    "captcha",
    ["trois", "TROIS", " trois "],
)
def test_send_contact_mail_with_valid_captcha(client, captcha, mailoutbox, settings):
    settings.DEFAULT_FROM_EMAIL = "impact@example.com"
    settings.CONTACT_EMAIL = "contact@example.com"

    subject = "Bonjour"
    message = "Bonjour Impact"
    email = "user@example.com"

    response = client.post(
        "/contact",
        data={"subject": subject, "message": message, "email": email, "sum": captcha},
        follow=True,
    )

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Votre message a bien été envoyé" in content

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.from_email == "impact@example.com"
    assert list(mail.to) == ["contact@example.com"]
    assert list(mail.reply_to) == [email]
    assert mail.subject == subject
    assert (
        mail.body
        == f"Ce message a été envoyé par {email} depuis http://testserver/contact :\n\n{message}"
    )


def test_send_contact_mail_with_invalid_captcha(client, mailoutbox, settings):
    settings.DEFAULT_FROM_EMAIL = "impact@example.com"
    settings.CONTACT_EMAIL = "contact@example.com"

    subject = "Bonjour"
    message = "Bonjour Impact"
    email = "user@example.com"
    sum = "mauvaise réponse"

    response = client.post(
        "/contact",
        data={"subject": subject, "message": message, "email": email, "sum": sum},
        follow=True,
    )

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert "L'envoi du message a échoué" in content
    assert len(mailoutbox) == 0


def test_send_contact_mail_with_numerical_captcha(client, mailoutbox, settings):
    settings.DEFAULT_FROM_EMAIL = "impact@example.com"
    settings.CONTACT_EMAIL = "contact@example.com"

    subject = "Bonjour"
    message = "Bonjour Impact"
    email = "user@example.com"
    sum = "3"

    response = client.post(
        "/contact",
        data={"subject": subject, "message": message, "email": email, "sum": sum},
        follow=True,
    )

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert "L'envoi du message a échoué" in content
    assert "La réponse doit être écrite en toutes lettres"
    assert len(mailoutbox) == 0


def test_page_mentions_legales(client):
    response = client.get("/mentions-legales")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page mentions legales -->" in content


def test_page_politique_confidentialite(client):
    response = client.get("/politique-confidentialite")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page politique de confidentialite -->" in content


def test_page_cgu(client):
    response = client.get("/cgu")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page cgu -->" in content


def test_succes_recherche_siren(client, mocker):
    SIREN = "123456789"
    RAISON_SOCIALE = "ENTREPRISE_TEST"
    mocker.patch(
        "api.recherche_entreprises.recherche",
        return_value={
            "siren": SIREN,
            "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
            "denomination": RAISON_SOCIALE,
        },
    )
    response = client.get("/simulation", {"siren": SIREN})

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert SIREN in content
    assert RAISON_SOCIALE in content
    assert "<!-- page simulation étape 2 -->" in content


def test_erreur_recherche_siren__siren_incorrect(client, mocker):
    SIREN = "123456789"
    mocker.patch(
        "api.recherche_entreprises.recherche",
        side_effect=api.exceptions.SirenError("MESSAGE"),
    )
    response = client.get("/simulation", {"siren": SIREN})

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "MESSAGE" in content
    assert "SIREN introuvable" in content
    assert "<!-- page simulation étape 1 -->" in content


def test_erreur_recherche_siren__erreur_api(client, mocker):
    SIREN = "123456789"
    mocker.patch(
        "api.recherche_entreprises.recherche",
        side_effect=api.exceptions.APIError("MESSAGE"),
    )
    response = client.get("/simulation", {"siren": SIREN})

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "MESSAGE" in content
    assert "SIREN introuvable" not in content
    assert "<!-- page simulation étape 1 -->" in content
