from public.forms import EligibiliteForm, RAISON_SOCIALE_MAX_LENGTH


def test_index(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "<!-- page index -->" in str(response.content)


def test_eligibilite_form(db):
    form = EligibiliteForm(
        data={
            "effectif": "grand",
            "bdese_accord": False,
            "raison_sociale": "a" * (RAISON_SOCIALE_MAX_LENGTH + 1),
            "siren": "123456789",
        }
    )

    assert form.is_valid()
