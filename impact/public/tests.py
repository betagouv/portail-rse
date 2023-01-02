from django.conf import settings

from public.forms import EligibiliteForm, RAISON_SOCIALE_MAX_LENGTH


def test_page_index(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "<!-- page index -->" in str(response.content)


def test_page_entreprise(client):
    response = client.get("/entreprise")

    assert response.status_code == 200
    assert "<!-- page entreprise -->" in str(response.content)


def test_page_contact(client):
    response = client.get("/contact")

    assert response.status_code == 200
    assert "<!-- page contact -->" in str(response.content)


def test_send_contact_mail(client, mailoutbox):
    subject = "Bonjour"
    message = "Bonjour Impact"
    from_email = "user@example.com"

    response = client.post(
        "/contact",
        data={"subject": subject, "message": message, "from_email": from_email},
        follow=True,
    )

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Votre message a bien été envoyé" in content
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.subject == subject
    assert mail.body == message
    assert mail.from_email == from_email
    assert list(mail.to) == [settings.CONTACT_EMAIL]


def test_page_mentions_legales(client):
    response = client.get("/mentions-legales")

    assert response.status_code == 200
    assert "<!-- page mentions legales -->" in str(response.content)


def test_page_donnees_personnelles(client):
    response = client.get("/donnees-personnelles")

    assert response.status_code == 200
    assert "<!-- page donnees personnelles -->" in str(response.content)


def test_page_cgu(client):
    response = client.get("/cgu")

    assert response.status_code == 200
    assert "<!-- page cgu -->" in str(response.content)


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
