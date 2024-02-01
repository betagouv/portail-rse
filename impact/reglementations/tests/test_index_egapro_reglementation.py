import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from freezegun import freeze_time

from api.tests.fixtures import mock_api_index_egapro  # noqa
from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from reglementations.models import derniere_annee_a_publier_index_egapro
from reglementations.views.base import ReglementationStatus
from reglementations.views.index_egapro import IndexEgaproReglementation


def test_reglementation_info():
    info = IndexEgaproReglementation.info()

    assert info["title"] == "Index de l’égalité professionnelle"
    assert (
        info["description"]
        == "Afin de lutter contre les inégalités salariales entre les femmes et les hommes, certaines entreprises doivent calculer et transmettre un index mesurant l’égalité salariale au sein de leur structure."
    )
    assert info["more_info_url"] == reverse("reglementations:fiche_index_egapro")
    assert info["tag"] == "tag-social"


def test_est_suffisamment_qualifiee(entreprise_non_qualifiee):
    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise_non_qualifiee,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
    )

    assert IndexEgaproReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_sans_effectif(entreprise_non_qualifiee):
    caracteristiques = CaracteristiquesAnnuelles(entreprise=entreprise_non_qualifiee)

    assert not IndexEgaproReglementation.est_suffisamment_qualifiee(caracteristiques)


@pytest.mark.parametrize("est_soumis", [True, False])
def test_calculate_status_with_not_authenticated_user(
    est_soumis, entreprise_factory, mocker
):
    entreprise = entreprise_factory()
    login_url = f"{reverse('users:login')}?next={reverse('reglementations:tableau_de_bord', args=[entreprise.siren])}"

    mocker.patch(
        "reglementations.views.index_egapro.IndexEgaproReglementation.est_soumis",
        return_value=est_soumis,
    )
    status = IndexEgaproReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, AnonymousUser()
    )

    if est_soumis:
        assert status.status == ReglementationStatus.STATUS_SOUMIS
        assert (
            status.status_detail
            == f'<a href="{login_url}">Vous êtes soumis à cette réglementation. Connectez-vous pour en savoir plus.</a>'
        )
    else:
        assert status.status == ReglementationStatus.STATUS_NON_SOUMIS
        assert status.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    assert (
        status.primary_action.url
        == "https://egapro.travail.gouv.fr/index-egapro/recherche"
    )
    assert (
        status.primary_action.title == "Consulter les index sur la plateforme nationale"
    )
    assert status.primary_action.external
    assert status.secondary_actions == []


@pytest.mark.parametrize("est_soumis", [True, False])
def test_calculate_status_with_not_attached_user(
    est_soumis, entreprise_factory, alice, mocker
):
    entreprise = entreprise_factory()

    mocker.patch(
        "reglementations.views.index_egapro.IndexEgaproReglementation.est_soumis",
        return_value=est_soumis,
    )
    status = IndexEgaproReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    if est_soumis:
        assert status.status == ReglementationStatus.STATUS_SOUMIS
        assert (
            status.status_detail == "L'entreprise est soumise à cette réglementation."
        )
    else:
        assert status.status == ReglementationStatus.STATUS_NON_SOUMIS
        assert (
            status.status_detail
            == "L'entreprise n'est pas soumise à cette réglementation."
        )
    assert status.primary_action is None
    assert status.secondary_actions == []


def test_calculate_status_less_than_50_employees(
    entreprise_factory, alice, mock_api_index_egapro
):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    index = IndexEgaproReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert index.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert index.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    assert (
        index.primary_action.url
        == "https://egapro.travail.gouv.fr/index-egapro/recherche"
    )
    assert (
        index.primary_action.title == "Consulter les index sur la plateforme nationale"
    )
    assert index.primary_action.external
    assert not mock_api_index_egapro.called


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calculate_status_more_than_50_employees(
    effectif, entreprise_factory, alice, mock_api_index_egapro
):
    entreprise = entreprise_factory(effectif=effectif)
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    mock_api_index_egapro.return_value = False
    with freeze_time("2023-02-28"):
        annee = derniere_annee_a_publier_index_egapro()
        index = IndexEgaproReglementation.calculate_status(
            entreprise.dernieres_caracteristiques_qualifiantes, alice
        )

    assert index.status == ReglementationStatus.STATUS_A_ACTUALISER
    assert (
        index.status_detail
        == f"Vous êtes soumis à cette réglementation car votre effectif est supérieur à 50 salariés. Vous n'avez pas encore publié votre index {annee} sur la plateforme Egapro. Vous devez calculer et publier votre index chaque année au plus tard le 1er mars."
    )
    assert index.prochaine_echeance == "01/03/2023"
    assert index.primary_action.url == "https://egapro.travail.gouv.fr/"
    assert index.primary_action.title == "Publier mon index sur la plateforme nationale"
    assert index.primary_action.external
    mock_api_index_egapro.assert_called_once_with(entreprise.siren, annee)

    mock_api_index_egapro.reset_mock()
    mock_api_index_egapro.return_value = True
    with freeze_time("2023-02-28"):
        annee = derniere_annee_a_publier_index_egapro()
        index = IndexEgaproReglementation.calculate_status(
            entreprise.dernieres_caracteristiques_qualifiantes, alice
        )

    assert index.status == ReglementationStatus.STATUS_A_JOUR
    assert (
        index.status_detail
        == f"Vous êtes soumis à cette réglementation car votre effectif est supérieur à 50 salariés. Vous avez publié votre index {annee} d'après les données disponibles sur la plateforme Egapro."
    )
    assert index.prochaine_echeance == "01/03/2024"
    mock_api_index_egapro.assert_called_once_with(entreprise.siren, annee)
