import html

import pytest
from django.urls import reverse

from reglementations.views.audit_energetique import AuditEnergetiqueReglementation
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.bges import BGESReglementation
from reglementations.views.dispositif_alerte import DispositifAlerteReglementation
from reglementations.views.dispositif_anticorruption import DispositifAntiCorruption
from reglementations.views.index_egapro import IndexEgaproReglementation

REGLEMENTATIONS = (
    BDESEReglementation,
    IndexEgaproReglementation,
    DispositifAlerteReglementation,
    BGESReglementation,
    AuditEnergetiqueReglementation,
    DispositifAntiCorruption,
)


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


def test_page_publique_des_reglementations(client):
    response = client.get("/reglementations")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "<!-- page reglementations -->" in content
    assert "BDESE" in content
    assert "Index de l’égalité professionnelle" in content

    context = response.context
    for index, REGLEMENTATION in enumerate(REGLEMENTATIONS):
        assert context["reglementations"][index]["reglementation"] == REGLEMENTATION
        assert context["reglementations"][index]["status"] is None