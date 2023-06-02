import pytest
from django.contrib.auth.models import AnonymousUser

from api.tests.fixtures import mock_api_recherche_entreprises  # noqa
from entreprises.models import Entreprise
from entreprises.models import Evolution
from entreprises.models import get_current_evolution
from entreprises.tests.conftest import unqualified_entreprise  # noqa
from habilitations.models import attach_user_to_entreprise
from reglementations.views import BDESEReglementation
from reglementations.views import IndexEgaproReglementation


def test_public_reglementations(client):
    response = client.get("/reglementations")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "<!-- page reglementations -->" in content
    assert "BDESE" in content
    assert "Index de l’égalité professionnelle" in content

    context = response.context
    assert context["entreprise"] is None
    assert context["reglementations"][0]["info"] == BDESEReglementation.info()
    assert context["reglementations"][0]["status"] is None
    assert context["reglementations"][1]["info"] == IndexEgaproReglementation.info()
    assert context["reglementations"][1]["status"] is None


@pytest.mark.parametrize("status_is_soumis", [True, False])
@pytest.mark.django_db
def test_public_reglementations_with_entreprise_data(status_is_soumis, client, mocker):
    data = {
        "effectif": Entreprise.EFFECTIF_MOINS_DE_50,
        "bdese_accord": False,
        "denomination": "Entreprise SAS",
        "siren": "000000001",
    }

    mocker.patch(
        "reglementations.views.BDESEReglementation.is_soumis",
        return_value=status_is_soumis,
        new_callable=mocker.PropertyMock,
    )
    mocker.patch(
        "reglementations.views.IndexEgaproReglementation.is_soumis",
        return_value=status_is_soumis,
        new_callable=mocker.PropertyMock,
    )
    response = client.get("/reglementations", data=data)

    content = response.content.decode("utf-8")
    assert "Entreprise SAS" in content

    # entreprise has been created
    entreprise = Entreprise.objects.get(siren="000000001")
    assert entreprise.denomination == "Entreprise SAS"
    evolution = get_current_evolution(entreprise)
    assert not evolution.bdese_accord
    assert evolution.effectif == Entreprise.EFFECTIF_MOINS_DE_50

    # reglementations for this entreprise are anonymously displayed
    context = response.context
    assert context["entreprise"] == entreprise
    reglementations = context["reglementations"]
    assert reglementations[0]["status"] == BDESEReglementation(
        entreprise
    ).calculate_status(2022, AnonymousUser())
    assert reglementations[1]["status"] == IndexEgaproReglementation(
        entreprise
    ).calculate_status(2022, AnonymousUser())

    if status_is_soumis:
        assert '<p class="fr-badge">soumis</p>' in content, content
        anonymous_status_detail = "Vous êtes soumis à cette réglementation. Connectez-vous pour en savoir plus."
        assert anonymous_status_detail in content, content
    else:
        assert '<p class="fr-badge">non soumis</p>' in content, content
        anonymous_status_detail = "Vous n'êtes pas soumis à cette réglementation."
        assert anonymous_status_detail in content, content


@pytest.fixture
def entreprise(db, alice):
    entreprise = Entreprise.objects.create(
        siren="000000001",
        denomination="Entreprise SAS",
    )
    Evolution.objects.create(
        annee=2023,
        entreprise=entreprise,
        effectif=Entreprise.EFFECTIF_MOINS_DE_50,
        bdese_accord=False,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    return entreprise


def test_reglementations_with_authenticated_user(client, entreprise):
    client.force_login(entreprise.users.first())

    response = client.get("/reglementations", follow=True)

    assert response.status_code == 200

    url = f"/reglementations/{entreprise.siren}"
    assert response.redirect_chain == [(url, 302)]


@pytest.mark.parametrize("status_is_soumis", [True, False])
def test_reglementations_with_authenticated_user_and_another_entreprise_data(
    status_is_soumis, client, entreprise, mocker
):
    """
    Ce cas est encore accessible mais ne correspond pas à un parcours utilisateur normal
    """
    client.force_login(entreprise.users.first())

    data = {
        "effectif": Entreprise.EFFECTIF_ENTRE_300_ET_499,
        "bdese_accord": False,
        "denomination": "Une autre entreprise SAS",
        "siren": "000000002",
    }

    mocker.patch(
        "reglementations.views.BDESEReglementation.is_soumis",
        return_value=status_is_soumis,
        new_callable=mocker.PropertyMock,
    )
    mocker.patch(
        "reglementations.views.IndexEgaproReglementation.is_soumis",
        return_value=status_is_soumis,
        new_callable=mocker.PropertyMock,
    )
    response = client.get("/reglementations", data=data)

    content = response.content.decode("utf-8")
    assert "Une autre entreprise SAS" in content

    reglementations = response.context["reglementations"]
    if status_is_soumis:
        assert '<p class="fr-badge">soumis</p>' in content
        anonymous_status_detail = "L'entreprise est soumise à cette réglementation."
        assert anonymous_status_detail in content, content
    else:
        assert '<p class="fr-badge">non soumis</p>' in content
        anonymous_status_detail = (
            "L'entreprise n'est pas soumise à cette réglementation."
        )
        assert anonymous_status_detail in content, content


def test_entreprise_data_are_saved_only_when_entreprise_user_is_autenticated(
    client, entreprise
):
    """
    Ce cas est encore accessible mais ne correspond pas à un parcours utilisateur normal
    """
    data = {
        "effectif": Entreprise.EFFECTIF_ENTRE_300_ET_499,
        "bdese_accord": False,
        "denomination": "Entreprise SAS",
        "siren": "000000001",
    }

    client.get("/reglementations", data=data)

    entreprise = Entreprise.objects.get(siren="000000001")

    assert get_current_evolution(entreprise).effectif == Entreprise.EFFECTIF_MOINS_DE_50

    client.force_login(entreprise.users.first())
    client.get("/reglementations", data=data)

    entreprise = Entreprise.objects.get(siren="000000001")
    assert (
        get_current_evolution(entreprise).effectif
        == Entreprise.EFFECTIF_ENTRE_300_ET_499
    )


def test_reglementation_with_authenticated_user(client, entreprise):
    client.force_login(entreprise.users.first())

    response = client.get(f"/reglementations/{entreprise.siren}")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    context = response.context
    assert context["entreprise"] == entreprise
    reglementations = context["reglementations"]
    assert reglementations[0]["status"] == BDESEReglementation(
        entreprise
    ).calculate_status(2022, entreprise.users.first())
    assert reglementations[1]["status"] == IndexEgaproReglementation(
        entreprise
    ).calculate_status(2022, entreprise.users.first())
    for reglementation in reglementations:
        assert reglementation["status"].status_detail in content


def test_reglementation_with_authenticated_user_and_multiple_entreprises(
    client, entreprise_factory, alice
):
    entreprise1 = entreprise_factory(siren="000000001")
    entreprise2 = entreprise_factory(siren="000000002")
    entreprise1.users.add(alice)
    entreprise2.users.add(alice)
    client.force_login(alice)

    response = client.get(f"/reglementations/{entreprise1.siren}")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    context = response.context
    assert context["entreprise"] == entreprise1
    reglementations = context["reglementations"]
    assert reglementations[0]["status"] == BDESEReglementation(
        entreprise1
    ).calculate_status(2022, alice)
    assert reglementations[1]["status"] == IndexEgaproReglementation(
        entreprise1
    ).calculate_status(2022, alice)
    for reglementation in reglementations:
        assert reglementation["status"].status_detail in content

    response = client.get(f"/reglementations/{entreprise2.siren}")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    context = response.context
    assert context["entreprise"] == entreprise2
    reglementations = context["reglementations"]
    assert reglementations[0]["status"] == BDESEReglementation(
        entreprise2
    ).calculate_status(2022, alice)
    assert reglementations[1]["status"] == IndexEgaproReglementation(
        entreprise2
    ).calculate_status(2022, alice)
    for reglementation in reglementations:
        assert reglementation["status"].status_detail in content


def test_reglementation_with_unqualified_entreprise_redirect_to_qualification_page(
    client, alice, unqualified_entreprise, mock_api_recherche_entreprises
):
    attach_user_to_entreprise(alice, unqualified_entreprise, "Présidente")
    client.force_login(alice)

    response = client.get(
        f"/reglementations/{unqualified_entreprise.siren}", follow=True
    )

    assert response.status_code == 200
    url = f"/entreprises/{unqualified_entreprise.siren}"
    assert response.redirect_chain == [(url, 302)]
