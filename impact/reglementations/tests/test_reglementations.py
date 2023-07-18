import pytest
from django.contrib.auth.models import AnonymousUser

from api.tests.fixtures import mock_api_recherche_entreprises  # noqa
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from habilitations.models import attach_user_to_entreprise
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.dispositif_alerte import DispositifAlerteReglementation
from reglementations.views.index_egapro import IndexEgaproReglementation


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
    assert (
        context["reglementations"][2]["info"] == DispositifAlerteReglementation.info()
    )
    assert context["reglementations"][2]["status"] is None


@pytest.mark.parametrize("status_est_soumis", [True, False])
@pytest.mark.django_db
def test_public_reglementations_with_entreprise_data(status_est_soumis, client, mocker):
    data = {
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        "bdese_accord": False,
        "denomination": "Entreprise SAS",
        "siren": "000000001",
    }

    mocker.patch(
        "reglementations.views.bdese.BDESEReglementation.est_soumis",
        return_value=status_est_soumis,
    )
    mocker.patch(
        "reglementations.views.index_egapro.IndexEgaproReglementation.est_soumis",
        return_value=status_est_soumis,
    )
    mocker.patch(
        "reglementations.views.dispositif_alerte.DispositifAlerteReglementation.est_soumis",
        return_value=status_est_soumis,
    )
    response = client.get("/reglementations", data=data)

    content = response.content.decode("utf-8")
    assert "Entreprise SAS" in content

    # entreprise has been created
    entreprise = Entreprise.objects.get(siren="000000001")
    assert entreprise.denomination == "Entreprise SAS"
    caracteristiques = entreprise.caracteristiques_actuelles()
    assert not caracteristiques.bdese_accord
    assert caracteristiques.effectif == CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50

    # reglementations for this entreprise are anonymously displayed
    context = response.context
    assert context["entreprise"] == entreprise
    reglementations = context["reglementations"]
    assert reglementations[0]["status"] == BDESEReglementation(
        entreprise
    ).calculate_status(caracteristiques, AnonymousUser())
    assert reglementations[1]["status"] == IndexEgaproReglementation(
        entreprise
    ).calculate_status(caracteristiques, AnonymousUser())
    assert reglementations[2]["status"] == DispositifAlerteReglementation(
        entreprise
    ).calculate_status(caracteristiques, AnonymousUser())

    if status_est_soumis:
        assert '<p class="fr-badge">soumis</p>' in content, content
        anonymous_status_detail = "Vous êtes soumis à cette réglementation. Connectez-vous pour en savoir plus."
        assert anonymous_status_detail in content, content
        assert '<p class="fr-badge">non soumis</p>' not in content, content
    else:
        assert '<p class="fr-badge">non soumis</p>' in content, content
        anonymous_status_detail = "Vous n'êtes pas soumis à cette réglementation."
        assert anonymous_status_detail in content, content
        assert '<p class="fr-badge">soumis</p>' not in content, content


@pytest.fixture
def entreprise(db, alice, entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        denomination="Entreprise SAS",
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
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


@pytest.mark.parametrize("status_est_soumis", [True, False])
def test_reglementations_with_authenticated_user_and_another_entreprise_data(
    status_est_soumis, client, entreprise, mocker
):
    """
    Ce cas est encore accessible mais ne correspond pas à un parcours utilisateur normal
    """
    client.force_login(entreprise.users.first())

    data = {
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        "bdese_accord": False,
        "denomination": "Une autre entreprise SAS",
        "siren": "000000002",
    }

    mocker.patch(
        "reglementations.views.bdese.BDESEReglementation.est_soumis",
        return_value=status_est_soumis,
    )
    mocker.patch(
        "reglementations.views.index_egapro.IndexEgaproReglementation.est_soumis",
        return_value=status_est_soumis,
    )
    mocker.patch(
        "reglementations.views.dispositif_alerte.DispositifAlerteReglementation.est_soumis",
        return_value=status_est_soumis,
    )
    response = client.get("/reglementations", data=data)

    content = response.content.decode("utf-8")
    assert "Une autre entreprise SAS" in content

    reglementations = response.context["reglementations"]
    if status_est_soumis:
        assert '<p class="fr-badge">soumis</p>' in content
        anonymous_status_detail = "L'entreprise est soumise à cette réglementation."
        assert anonymous_status_detail in content, content
    else:
        assert '<p class="fr-badge">non soumis</p>' in content
        anonymous_status_detail = (
            "L'entreprise n'est pas soumise à cette réglementation."
        )
        assert anonymous_status_detail in content, content


def test_entreprise_data_are_saved_only_when_entreprise_user_is_authenticated(
    client, entreprise, entreprise_factory
):
    """
    La simulation par un utilisateur anonyme sur une entreprise déjà enregistrée en base ne modifie pas en base son évolution
    mais affiche quand même à l'utilisateur anonyme les statuts correspondant aux données utilisées lors de la simulation
    """
    effectif = CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499
    data = {
        "effectif": effectif,
        "bdese_accord": False,
        "denomination": entreprise.denomination,
        "siren": entreprise.siren,
    }

    response = client.get("/reglementations", data=data)

    entreprise.refresh_from_db()
    assert (
        entreprise.caracteristiques_actuelles().effectif
        == CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50
    )

    context = response.context
    assert context["entreprise"] == entreprise
    bdese_status = context["reglementations"][0]["status"]
    index_egapro_status = context["reglementations"][1]["status"]
    dispositif_alerte_status = context["reglementations"][2]["status"]
    caracteristiques = CaracteristiquesAnnuelles(
        annee=2022, entreprise=entreprise, effectif=effectif, bdese_accord=False
    )
    assert bdese_status == BDESEReglementation(entreprise).calculate_status(
        caracteristiques, AnonymousUser()
    )
    assert index_egapro_status == IndexEgaproReglementation(
        entreprise
    ).calculate_status(caracteristiques, AnonymousUser())
    assert dispositif_alerte_status == DispositifAlerteReglementation(
        entreprise
    ).calculate_status(caracteristiques, AnonymousUser())

    # si c'est un utilisateur rattaché à l'entreprise qui fait la simulation en changeant les données d'évolution
    # on enregistre ces nouvelles données en base
    # ce cas est encore accessible mais ne correspond pas à un parcours utilisateur normal
    client.force_login(entreprise.users.first())
    client.get("/reglementations", data=data)

    entreprise.refresh_from_db()
    assert (
        entreprise.caracteristiques_actuelles().effectif
        == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499
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
    ).calculate_status(
        entreprise.caracteristiques_actuelles(), entreprise.users.first()
    )
    assert reglementations[1]["status"] == IndexEgaproReglementation(
        entreprise
    ).calculate_status(
        entreprise.caracteristiques_actuelles(), entreprise.users.first()
    )
    assert reglementations[2]["status"] == DispositifAlerteReglementation(
        entreprise
    ).calculate_status(
        entreprise.caracteristiques_actuelles(), entreprise.users.first()
    )
    for reglementation in reglementations:
        assert reglementation["status"].status_detail in content


def test_reglementation_with_authenticated_user_and_multiple_entreprises(
    client, entreprise_factory, alice
):
    entreprise1 = entreprise_factory(siren="000000001")
    entreprise2 = entreprise_factory(siren="000000002")
    attach_user_to_entreprise(alice, entreprise1, "Présidente")
    attach_user_to_entreprise(alice, entreprise2, "Présidente")
    client.force_login(alice)

    response = client.get(f"/reglementations/{entreprise1.siren}")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    context = response.context
    assert context["entreprise"] == entreprise1
    reglementations = context["reglementations"]
    assert reglementations[0]["status"] == BDESEReglementation(
        entreprise1
    ).calculate_status(entreprise1.caracteristiques_actuelles(), alice)
    assert reglementations[1]["status"] == IndexEgaproReglementation(
        entreprise1
    ).calculate_status(entreprise1.caracteristiques_actuelles(), alice)
    assert reglementations[2]["status"] == DispositifAlerteReglementation(
        entreprise1
    ).calculate_status(entreprise1.caracteristiques_actuelles(), alice)
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
    ).calculate_status(entreprise2.caracteristiques_actuelles(), alice)
    assert reglementations[1]["status"] == IndexEgaproReglementation(
        entreprise2
    ).calculate_status(entreprise2.caracteristiques_actuelles(), alice)
    assert reglementations[2]["status"] == DispositifAlerteReglementation(
        entreprise2
    ).calculate_status(entreprise2.caracteristiques_actuelles(), alice)
    for reglementation in reglementations:
        assert reglementation["status"].status_detail in content


def test_reglementation_with_entreprise_non_qualifiee_redirect_to_qualification_page(
    client, alice, entreprise_non_qualifiee, mock_api_recherche_entreprises
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    client.force_login(alice)

    response = client.get(
        f"/reglementations/{entreprise_non_qualifiee.siren}", follow=True
    )

    assert response.status_code == 200
    url = f"/entreprises/{entreprise_non_qualifiee.siren}"
    assert response.redirect_chain == [(url, 302)]
