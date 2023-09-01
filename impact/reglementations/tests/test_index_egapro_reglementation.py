import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from api.tests.fixtures import mock_api_index_egapro  # noqa
from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from reglementations.models import derniere_annee_a_remplir_index_egapro
from reglementations.views.base import ReglementationStatus
from reglementations.views.index_egapro import IndexEgaproReglementation


def test_index_egapro_reglementation_info():
    info = IndexEgaproReglementation.info()

    assert info["title"] == "Index de l’égalité professionnelle"
    assert (
        info["description"]
        == "Afin de lutter contre les inégalités salariales entre les femmes et les hommes, certaines entreprises doivent calculer et transmettre un index mesurant l’égalité salariale au sein de leur structure."
    )
    assert (
        info["more_info_url"]
        == "https://www.economie.gouv.fr/entreprises/index-egalite-professionnelle-obligatoire"
    )


def test_calculate_status_with_not_authenticated_user(entreprise_factory, mocker):
    entreprise = entreprise_factory()

    mocker.patch(
        "reglementations.views.index_egapro.IndexEgaproReglementation.est_soumis",
        return_value=False,
    )
    status = IndexEgaproReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, AnonymousUser()
    )

    assert status.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert status.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    assert (
        status.primary_action.url
        == "https://egapro.travail.gouv.fr/index-egapro/recherche"
    )
    assert status.primary_action.title == "Consulter les index sur la plateforme Egapro"
    assert status.primary_action.external
    assert status.secondary_actions == []

    mocker.patch(
        "reglementations.views.index_egapro.IndexEgaproReglementation.est_soumis",
        return_value=True,
    )
    status = IndexEgaproReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, AnonymousUser()
    )

    assert status.status == ReglementationStatus.STATUS_SOUMIS
    login_url = f"{reverse('users:login')}?next={reverse('reglementations:reglementations', args=[entreprise.siren])}"

    assert (
        status.status_detail
        == f'<a href="{login_url}">Vous êtes soumis à cette réglementation. Connectez-vous pour en savoir plus.</a>'
    )
    assert status.primary_action.title == "Se connecter"
    assert status.primary_action.url == login_url
    assert status.secondary_actions == []


def test_calculate_status_with_not_attached_user(entreprise_factory, alice, mocker):
    entreprise = entreprise_factory()

    mocker.patch(
        "reglementations.views.index_egapro.IndexEgaproReglementation.est_soumis",
        return_value=False,
    )
    status = IndexEgaproReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert status.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        status.status_detail == "L'entreprise n'est pas soumise à cette réglementation."
    )
    assert status.primary_action is None
    assert status.secondary_actions == []

    mocker.patch(
        "reglementations.views.index_egapro.IndexEgaproReglementation.est_soumis",
        return_value=True,
    )
    status = IndexEgaproReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert status.status == ReglementationStatus.STATUS_SOUMIS
    assert status.status_detail == "L'entreprise est soumise à cette réglementation."
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
    assert index.primary_action.title == "Consulter les index sur la plateforme Egapro"
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
    annee = derniere_annee_a_remplir_index_egapro()

    mock_api_index_egapro.return_value = False
    index = IndexEgaproReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert index.status == ReglementationStatus.STATUS_A_ACTUALISER
    assert (
        index.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 50 salariés. Vous n'avez pas encore déclaré votre index sur la plateforme Egapro."
    )
    assert index.primary_action.url == "https://egapro.travail.gouv.fr/"
    assert (
        index.primary_action.title
        == "Calculer et déclarer mon index sur la plateforme Egapro"
    )
    assert index.primary_action.external
    mock_api_index_egapro.assert_called_once_with(entreprise.siren, annee)

    mock_api_index_egapro.reset_mock()
    mock_api_index_egapro.return_value = True
    index = IndexEgaproReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert index.status == ReglementationStatus.STATUS_A_JOUR
    assert (
        index.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 50 salariés. Vous avez rempli vos obligations d'après les données disponibles sur la plateforme Egapro."
    )
    mock_api_index_egapro.assert_called_once_with(
        entreprise.siren, derniere_annee_a_remplir_index_egapro()
    )
