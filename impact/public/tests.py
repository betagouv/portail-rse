from public.forms import EligibiliteForm, RAISON_SOCIALE_MAX_LENGTH


def test_page_index(client):
    response = client.get("/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page index -->" in content


def test_page_entreprise(client):
    response = client.get("/entreprise")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page entreprise -->" in content


def test_page_contact(client):
    response = client.get("/contact")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page contact -->" in content


def test_send_contact_mail(client, mailoutbox, settings):
    settings.DEFAULT_FROM_EMAIL = "impact@example.com"
    settings.CONTACT_EMAIL = "contact@example.com"

    subject = "Bonjour"
    message = "Bonjour Impact"
    email = "user@example.com"

    response = client.post(
        "/contact",
        data={"subject": subject, "message": message, "email": email},
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
    form = EligibiliteForm(
        data={
            "effectif": "grand",
            "bdese_accord": False,
            "raison_sociale": "a" * (RAISON_SOCIALE_MAX_LENGTH + 1),
            "siren": "123456789",
        }
    )

    assert form.is_valid()

    entreprise = form.save()

    assert entreprise.raison_sociale == "a" * RAISON_SOCIALE_MAX_LENGTH
