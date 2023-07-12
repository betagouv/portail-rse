import json

import pytest

from api.tests.fixtures import mock_api_index_egapro  # noqa
from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from reglementations.models import derniere_annee_a_remplir_index_egapro
from reglementations.views.base import ReglementationStatus
from reglementations.views.index_egapro import IndexEgaproReglementation
from reglementations.views.index_egapro import is_index_egapro_published


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


def test_calculate_status_less_than_50_employees(
    entreprise_factory, alice, mock_api_index_egapro
):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    index = IndexEgaproReglementation(entreprise).calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert index.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert index.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    assert (
        index.primary_action.url
        == "https://egapro.travail.gouv.fr/index-egapro/recherche"
    )
    assert index.primary_action.title == "Consulter les index sur Egapro"
    assert index.primary_action.external
    assert not mock_api_index_egapro.called


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_500_ET_PLUS,
    ],
)
def test_calculate_status_more_than_50_employees(
    effectif, entreprise_factory, alice, mock_api_index_egapro
):
    entreprise = entreprise_factory(effectif=effectif)
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    annee = derniere_annee_a_remplir_index_egapro()

    mock_api_index_egapro.return_value = False
    index = IndexEgaproReglementation(entreprise).calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert index.status == ReglementationStatus.STATUS_A_ACTUALISER
    assert (
        index.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 50 salariés. Vous n'avez pas encore déclaré votre index sur la plateforme Egapro."
    )
    assert index.primary_action.url == "https://egapro.travail.gouv.fr/"
    assert index.primary_action.title == "Calculer et déclarer mon index sur Egapro"
    assert index.primary_action.external
    mock_api_index_egapro.assert_called_once_with(entreprise.siren, annee)

    mock_api_index_egapro.reset_mock()
    mock_api_index_egapro.return_value = True
    index = IndexEgaproReglementation(entreprise).calculate_status(
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


class MockedResponse:
    def __init__(self, content, status_code):
        self.content = content
        self.status_code = status_code

    def json(self):
        return json.loads(self.content)


def test_is_index_egapro_published_with_up_to_date_entreprise(
    grande_entreprise, mocker
):
    # Example response from https://egapro.travail.gouv.fr/api/public/declaration/552032534/2021
    index_egapro_data = """{"entreprise":{"siren":"552032534","r\u00e9gion":"\u00cele-de-France","code_naf":"70.10Z","effectif":{"total":867,"tranche":"251:999"},"d\u00e9partement":"Paris","raison_sociale":"DANONE"},"indicateurs":{"promotions":{"non_calculable":null,"note":15,"objectif_de_progression":null},"augmentations_et_promotions":{"non_calculable":null,"note":null,"objectif_de_progression":null},"r\u00e9mun\u00e9rations":{"non_calculable":null,"note":29,"objectif_de_progression":null},"cong\u00e9s_maternit\u00e9":{"non_calculable":null,"note":15,"objectif_de_progression":null},"hautes_r\u00e9mun\u00e9rations":{"non_calculable":null,"note":0,"objectif_de_progression":null,"r\u00e9sultat":1,"population_favorable":"femmes"}},"d\u00e9claration":{"index":79,"ann\u00e9e_indicateurs":2021,"mesures_correctives":null}}"""

    egapro_request = mocker.patch(
        "requests.get", return_value=MockedResponse(index_egapro_data, 200)
    )

    assert is_index_egapro_published(grande_entreprise)
    egapro_request.assert_called_once_with(
        f"https://egapro.travail.gouv.fr/api/public/declaration/{grande_entreprise.siren}/{derniere_annee_a_remplir_index_egapro()}"
    )


def test_is_index_egapro_not_published(grande_entreprise, mocker):
    # Example response from https://egapro.travail.gouv.fr/api/public/declaration/889297453/2020
    index_egapro_data = (
        """{"error":"No declaration with siren 889297453 and year 2020"}"""
    )
    egapro_request = mocker.patch(
        "requests.get", return_value=MockedResponse(index_egapro_data, 404)
    )

    assert not is_index_egapro_published(grande_entreprise)
    egapro_request.assert_called_once_with(
        f"https://egapro.travail.gouv.fr/api/public/declaration/{grande_entreprise.siren}/{derniere_annee_a_remplir_index_egapro()}"
    )
