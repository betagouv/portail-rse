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
