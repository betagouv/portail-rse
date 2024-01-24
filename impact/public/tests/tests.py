import html

import pytest
from django.urls import reverse

from habilitations.models import attach_user_to_entreprise
from reglementations.views import REGLEMENTATIONS


def test_page_index_pour_un_visiteur_anonyme(client):
    response = client.get("/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page index -->" in content


def test_redirection_de_la_page_index_vers_ses_reglementations_si_l_utilisateur_vient_de_se_connecter_depuis_la_page_d_accueil(
    client, alice, entreprise_factory
):
    entreprise = entreprise_factory()
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    client.force_login(alice)

    response = client.get(
        "/", follow=True, headers={"referer": "http://domain.test/connexion"}
    )

    assert response.status_code == 200
    assert response.redirect_chain == [
        (reverse("reglementations:tableau_de_bord", args=[entreprise.siren]), 302),
    ]

    response = client.get(
        "/", follow=True, headers={"referer": "http://domain.test/connexion?next=/"}
    )

    assert response.status_code == 200
    assert response.redirect_chain == [
        (reverse("reglementations:tableau_de_bord", args=[entreprise.siren]), 302),
    ]


def test_redirection_de_la_page_index_vers_l_ajout_d_entreprise_si_l_utilisateur_vient_de_se_connecter_depuis_la_page_d_accueil_et_sans_entreprise(
    client, alice
):
    """cas où un utilisateur aurait quitté toutes ses entreprises"""
    client.force_login(alice)
    response = client.get(
        "/", follow=True, headers={"referer": "http://domain.test/connexion?next=/"}
    )

    assert response.status_code == 200
    assert response.redirect_chain == [
        (reverse("entreprises:entreprises"), 302),
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
    settings.DEFAULT_FROM_EMAIL = "portail@example.com"
    settings.CONTACT_EMAIL = "contact@example.com"

    subject = "Bonjour"
    message = "Bonjour Utilisateur"
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
    assert mail.from_email == "portail@example.com"
    assert list(mail.to) == ["contact@example.com"]
    assert list(mail.reply_to) == [email]
    assert mail.subject == subject
    assert (
        mail.body
        == f"Ce message a été envoyé par {email} depuis http://testserver/contact :\n\n{message}"
    )


def test_send_contact_mail_with_invalid_captcha(client, mailoutbox, settings):
    settings.DEFAULT_FROM_EMAIL = "portail@example.com"
    settings.CONTACT_EMAIL = "contact@example.com"

    subject = "Bonjour"
    message = "Bonjour Utilisateur"
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
    settings.DEFAULT_FROM_EMAIL = "portail@example.com"
    settings.CONTACT_EMAIL = "contact@example.com"

    subject = "Bonjour"
    message = "Bonjour Utilisateur"
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


def test_page_stats(client):
    response = client.get("/stats")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page stats -->" in content


def test_page_publique_des_reglementations(client):
    response = client.get("/reglementations")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    context = response.context
    assert not context.get("entreprise")
    assert context["reglementations"] == REGLEMENTATIONS
    for REGLEMENTATION in REGLEMENTATIONS:
        assert REGLEMENTATION.title in content
