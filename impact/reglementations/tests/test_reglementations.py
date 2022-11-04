import pytest

from entreprises.models import Entreprise
from reglementations.views import BDESEReglementation, IndexEgaproReglementation


@pytest.fixture
def mock_index_egapro(mocker):
    mocker.patch("reglementations.views.is_index_egapro_updated", return_value=False)


def test_public_reglementations(client):
    response = client.get("/reglementations")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "<!-- page reglementations -->" in content
    assert "BDESE" in content
    assert "Index de l’égalité professionnelle" in content

    context = response.context
    assert len(context["entreprises"]) == 1
    entreprise = context["entreprises"][0]
    assert entreprise["entreprise"] is None
    assert entreprise["reglementations"][0] == BDESEReglementation()
    assert entreprise["reglementations"][1] == IndexEgaproReglementation()


@pytest.mark.django_db
def test_public_reglementations_with_entreprise_data(client, mock_index_egapro):
    data = {
        "effectif": "petit",
        "bdese_accord": False,
        "raison_sociale": "Entreprise SAS",
        "siren": "000000001",
    }

    response = client.get("/reglementations", data=data)

    content = response.content.decode("utf-8")
    assert "Entreprise SAS" in content

    # entreprise has been created
    entreprise = Entreprise.objects.get(siren="000000001")
    assert entreprise.raison_sociale == "Entreprise SAS"
    assert not entreprise.bdese_accord
    assert entreprise.effectif == "petit"

    # reglementations for this entreprise are displayed
    context = response.context
    assert len(context["entreprises"]) == 1
    context_entreprise = context["entreprises"][0]
    assert context_entreprise["entreprise"] == entreprise
    assert context_entreprise["reglementations"][0] == BDESEReglementation.calculate(
        entreprise
    )
    assert context_entreprise["reglementations"][
        1
    ] == IndexEgaproReglementation.calculate(entreprise)


@pytest.fixture
def entreprise(db, django_user_model):
    user = django_user_model.objects.create()
    entreprise = Entreprise.objects.create(
        siren="000000001",
        effectif="petit",
        bdese_accord=False,
        raison_sociale="Entreprise SAS",
    )
    entreprise.users.add(user)
    return entreprise


def test_reglementations_with_authenticated_user(client, mock_index_egapro, entreprise):
    client.force_login(entreprise.users.first())

    response = client.get("/reglementations")

    assert response.status_code == 200

    context = response.context
    assert len(context["entreprises"]) == 1
    context_entreprise = context["entreprises"][0]
    assert context_entreprise["entreprise"] == entreprise
    assert context_entreprise["reglementations"][0] == BDESEReglementation.calculate(
        entreprise
    )
    assert context_entreprise["reglementations"][
        1
    ] == IndexEgaproReglementation.calculate(entreprise)


def test_reglementations_with_authenticated_user_and_another_entreprise_data(
    client, mock_index_egapro, entreprise
):
    client.force_login(entreprise.users.first())

    data = {
        "effectif": "grand",
        "bdese_accord": False,
        "raison_sociale": "Une autre entreprise SAS",
        "siren": "000000002",
    }

    response = client.get("/reglementations", data=data)

    content = response.content.decode("utf-8")
    assert "Une autre entreprise SAS" in content
    assert not "Entreprise SAS" in content


def test_entreprise_data_are_saved_only_when_entreprise_user_is_autenticated(
    client, mock_index_egapro, entreprise
):
    data = {
        "effectif": "grand",
        "bdese_accord": False,
        "raison_sociale": "Entreprise SAS",
        "siren": "000000001",
    }

    client.get("/reglementations", data=data)

    entreprise = Entreprise.objects.get(siren="000000001")
    assert entreprise.effectif == "petit"

    client.force_login(entreprise.users.first())
    client.get("/reglementations", data=data)

    entreprise = Entreprise.objects.get(siren="000000001")
    assert entreprise.effectif == "grand"
