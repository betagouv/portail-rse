import json

import freezegun
import pytest

from entreprises.models import Evolution
from habilitations.models import attach_user_to_entreprise
from reglementations.views import IndexEgaproReglementation
from reglementations.views import is_index_egapro_updated
from reglementations.views import ReglementationStatus


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
    entreprise_factory, alice, mock_index_egapro
):
    entreprise = entreprise_factory(effectif=Evolution.EFFECTIF_MOINS_DE_50)
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    index = IndexEgaproReglementation(entreprise).calculate_status(2022, alice)

    assert index.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert index.status_detail == "Vous n'êtes pas soumis à cette réglementation"
    assert not mock_index_egapro.called


@pytest.mark.parametrize(
    "effectif",
    [
        Evolution.EFFECTIF_ENTRE_50_ET_299,
        Evolution.EFFECTIF_ENTRE_300_ET_499,
        Evolution.EFFECTIF_500_ET_PLUS,
    ],
)
def test_calculate_status_more_than_50_employees(
    effectif, entreprise_factory, alice, mock_index_egapro
):
    entreprise = entreprise_factory(effectif=effectif)
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    mock_index_egapro.return_value = False
    index = IndexEgaproReglementation(entreprise).calculate_status(2022, alice)

    assert index.status == ReglementationStatus.STATUS_A_ACTUALISER
    assert (
        index.status_detail
        == "Vous êtes soumis à cette réglementation. Vous n'avez pas encore déclaré votre index sur la plateforme Egapro."
    )
    assert index.primary_action
    mock_index_egapro.assert_called_once_with(entreprise)

    mock_index_egapro.reset_mock()
    mock_index_egapro.return_value = True
    index = IndexEgaproReglementation(entreprise).calculate_status(2022, alice)

    assert index.status == ReglementationStatus.STATUS_A_JOUR
    assert (
        index.status_detail
        == "Vous êtes soumis à cette réglementation. Vous avez rempli vos obligations d'après les données disponibles sur la plateforme Egapro."
    )
    assert index.primary_action
    mock_index_egapro.assert_called_once_with(entreprise)


class MockedResponse:
    def __init__(self, content, status_code):
        self.content = content
        self.status_code = status_code

    def json(self):
        return json.loads(self.content)


def test_is_index_egapro_updated_with_up_to_date_entreprise(grande_entreprise, mocker):
    # Example response from https://egapro.travail.gouv.fr/api/public/declaration/552032534/2021
    index_egapro_data = """{"entreprise":{"siren":"552032534","r\u00e9gion":"\u00cele-de-France","code_naf":"70.10Z","effectif":{"total":867,"tranche":"251:999"},"d\u00e9partement":"Paris","raison_sociale":"DANONE"},"indicateurs":{"promotions":{"non_calculable":null,"note":15,"objectif_de_progression":null},"augmentations_et_promotions":{"non_calculable":null,"note":null,"objectif_de_progression":null},"r\u00e9mun\u00e9rations":{"non_calculable":null,"note":29,"objectif_de_progression":null},"cong\u00e9s_maternit\u00e9":{"non_calculable":null,"note":15,"objectif_de_progression":null},"hautes_r\u00e9mun\u00e9rations":{"non_calculable":null,"note":0,"objectif_de_progression":null,"r\u00e9sultat":1,"population_favorable":"femmes"}},"d\u00e9claration":{"index":79,"ann\u00e9e_indicateurs":2021,"mesures_correctives":null}}"""

    egapro_request = mocker.patch(
        "requests.get", return_value=MockedResponse(index_egapro_data, 200)
    )

    with freezegun.freeze_time("2022-11-25"):
        assert is_index_egapro_updated(grande_entreprise)
    egapro_request.assert_called_once_with(
        f"https://egapro.travail.gouv.fr/api/public/declaration/{grande_entreprise.siren}/2021"
    )


def test_is_index_egapro_not_updated(grande_entreprise, mocker):
    # Example response from https://egapro.travail.gouv.fr/api/public/declaration/889297453/2020
    index_egapro_data = (
        """{"error":"No declaration with siren 889297453 and year 2020"}"""
    )

    egapro_request = mocker.patch(
        "requests.get", return_value=MockedResponse(index_egapro_data, 404)
    )

    with freezegun.freeze_time("2021-11-25"):
        assert not is_index_egapro_updated(grande_entreprise)
    egapro_request.assert_called_once_with(
        f"https://egapro.travail.gouv.fr/api/public/declaration/{grande_entreprise.siren}/2020"
    )
