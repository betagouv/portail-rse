from django.urls import reverse
import pytest

from reglementations.models import BDESE_50_300, BDESE_300


def test_bdese_is_not_public(client, django_user_model, grande_entreprise):
    url = f"/bdese/{grande_entreprise.siren}/1"
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("login")
    assert response.url == f"{connexion_url}?next={url}"

    user = django_user_model.objects.create()
    client.force_login(user)
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.parametrize(
    "effectif, bdese_class", [("moyen", BDESE_50_300), ("grand", BDESE_300)]
)
def test_bdese_is_created_at_first_authorized_request(
    effectif, bdese_class, client, django_user_model, entreprise_factory
):
    entreprise = entreprise_factory(effectif=effectif)
    user = django_user_model.objects.create()
    entreprise.users.add(user)
    client.force_login(user)

    assert not bdese_class.objects.filter(entreprise=entreprise)

    url = f"/bdese/{entreprise.siren}/1"
    response = client.get(url)

    assert response.status_code == 200
    bdese = bdese_class.objects.get(entreprise=entreprise)


@pytest.fixture
def authorized_user_client(client, django_user_model, grande_entreprise):
    user = django_user_model.objects.create()
    grande_entreprise.users.add(user)
    client.force_login(user)
    return client


def test_save_step_error(authorized_user_client, grande_entreprise):
    url = f"/bdese/{grande_entreprise.siren}/1"
    response = authorized_user_client.post(url, {"unite_absenteisme": "yolo"})

    assert response.status_code == 200
    assert (
        "L&#x27;étape n&#x27;a pas été enregistrée car le formulaire contient des erreurs"
        in response.content.decode("utf-8")
    )

    bdese = BDESE_300.objects.get(entreprise=grande_entreprise)
    assert bdese.unite_absenteisme != "yolo"


def test_save_step_as_draft_success(authorized_user_client, grande_entreprise):
    url = f"/bdese/{grande_entreprise.siren}/1"
    response = authorized_user_client.post(url, {"unite_absenteisme": "H"})

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "Étape enregistrée" in content
    assert "Enregistrer et marquer comme terminé" in content
    assert "Enregistrer en brouillon" in content

    bdese = BDESE_300.objects.get(entreprise=grande_entreprise)
    assert bdese.unite_absenteisme == "H"
    assert not bdese.step_is_complete(1)


def test_save_step_and_mark_as_complete_success(
    authorized_user_client, grande_entreprise
):
    url = f"/bdese/{grande_entreprise.siren}/1"
    response = authorized_user_client.post(
        url, {"unite_absenteisme": "H", "save_complete": ""}, follow=True
    )

    assert response.status_code == 200
    assert response.redirect_chain == [(url, 302)]

    content = response.content.decode("utf-8")
    assert "Étape enregistrée" in content
    assert "Repasser en brouillon pour modifier" in content

    bdese = BDESE_300.objects.get(entreprise=grande_entreprise)
    assert bdese.unite_absenteisme == "H"
    assert bdese.step_is_complete(1)


def test_mark_step_as_incomplete(authorized_user_client, grande_entreprise):
    bdese = BDESE_300.objects.create(entreprise=grande_entreprise)
    bdese.mark_step_as_complete(1)

    url = f"/bdese/{grande_entreprise.siren}/1"
    response = authorized_user_client.post(url, {"mark_incomplete": ""}, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(url, 302)]

    content = response.content.decode("utf-8")
    assert "Étape enregistrée" not in content
    assert "Enregistrer et marquer comme terminé" in content
    assert "Enregistrer en brouillon" in content

    bdese = BDESE_300.objects.get(entreprise=grande_entreprise)
    assert not bdese.step_is_complete(1)
