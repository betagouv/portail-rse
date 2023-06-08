import html

import pytest

import api.exceptions
from entreprises.models import Evolution
from public.forms import DENOMINATION_MAX_LENGTH
from public.forms import SimulationForm


def test_page_index(client):
    response = client.get("/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page index -->" in content


def test_page_simulation(client):
    response = client.get("/simulation")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page simulation étape 1 -->" in content


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


def test_eligibilite_form_truncate_raison_social_when_too_long(db):
    form = SimulationForm(
        data={
            "effectif": Evolution.EFFECTIF_ENTRE_300_ET_499,
            "bdese_accord": False,
            "denomination": "a" * (DENOMINATION_MAX_LENGTH + 1),
            "siren": "123456789",
        }
    )
    assert not form.is_valid()
    assert "denomination" in form.errors


def test_succes_recherche_siren(client, mocker):
    SIREN = "123456789"
    RAISON_SOCIALE = "ENTREPRISE_TEST"
    mocker.patch(
        "api.recherche_entreprises.recherche",
        return_value={
            "siren": SIREN,
            "effectif": Evolution.EFFECTIF_ENTRE_50_ET_299,
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
