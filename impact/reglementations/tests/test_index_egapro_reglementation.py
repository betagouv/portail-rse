import json

import freezegun
import pytest

from reglementations.views import IndexEgaproReglementation, is_index_egapro_updated


def test_default_index_egapro_reglementation():
    index = IndexEgaproReglementation()

    assert index.title == "Index de l’égalité professionnelle"
    assert (
        index.description
        == "Afin de lutter contre les inégalités salariales entre les femmes et les hommes, certaines entreprises doivent calculer et transmettre un index mesurant l’égalité salariale au sein de leur structure."
    )
    assert (
        index.more_info_url
        == "https://www.economie.gouv.fr/entreprises/index-egalite-professionnelle-obligatoire"
    )

    assert index.status is None
    assert index.status_detail is None
    assert index.primary_action.url == "https://egapro.travail.gouv.fr/"
    assert index.primary_action.title == "Calculer et déclarer mon index sur Egapro"
    assert index.primary_action.external == True


def test_calculate_less_than_50_employees(entreprise_factory, mock_index_egapro):
    entreprise = entreprise_factory(effectif="petit")

    index = IndexEgaproReglementation.calculate(entreprise)

    assert index.status == IndexEgaproReglementation.STATUS_NON_SOUMIS
    assert index.status_detail == "Vous n'êtes pas soumis à cette réglementation"
    assert not mock_index_egapro.called


@pytest.mark.parametrize("effectif", ["moyen", "grand", "sup500"])
def test_calculate_more_than_50_employees(
    effectif, entreprise_factory, mock_index_egapro
):
    entreprise = entreprise_factory(effectif=effectif)
    mock_index_egapro.return_value = False

    index = IndexEgaproReglementation.calculate(entreprise)

    assert index.status == IndexEgaproReglementation.STATUS_A_ACTUALISER
    assert (
        index.status_detail
        == "Vous êtes soumis à cette réglementation. Vous n'avez pas encore déclaré votre index sur la plateforme Egapro."
    )
    assert mock_index_egapro.called_once_with(entreprise)

    mock_index_egapro.return_value = True

    index = IndexEgaproReglementation.calculate(entreprise)

    assert index.status == IndexEgaproReglementation.STATUS_A_JOUR
    assert (
        index.status_detail
        == "Vous êtes soumis à cette réglementation. Vous avez rempli vos obligations d'après les données disponibles sur la plateforme Egapro."
    )
    assert mock_index_egapro.called_once_with(entreprise)


class MockedResponse:
    status_code = 200

    def __init__(self, content):
        self.content = content

    def json(self):
        return json.loads(self.content)


def test_is_index_egapro_updated_with_up_to_date_entreprise(grande_entreprise, mocker):
    # Example response from https://egapro.travail.gouv.fr/api/search?q=552032534
    index_egapro_data = """{"data":[{"entreprise":{"raison_sociale":"DANONE","siren":"552032534","r\u00e9gion":"11","d\u00e9partement":"75","code_naf":"70.10Z","ues":null,"effectif":{"tranche":"251:999"}},"notes":{"2018":80,"2019":78,"2020":84,"2021":79},"notes_remunerations":{"2018":35,"2019":23,"2020":29,"2021":29},"notes_augmentations":{"2018":10,"2019":20,"2020":20,"2021":20},"notes_promotions":{"2018":15,"2019":15,"2020":15,"2021":15},"notes_augmentations_et_promotions":{"2018":null,"2019":null,"2020":null,"2021":null},"notes_conges_maternite":{"2018":15,"2019":15,"2020":15,"2021":15},"notes_hautes_r\u00e9mun\u00e9rations":{"2018":5,"2019":5,"2020":5,"2021":0},"label":"DANONE"}],"count":1}"""

    mocker.patch("requests.get", return_value=MockedResponse(index_egapro_data))

    with freezegun.freeze_time("2022-11-25"):
        assert is_index_egapro_updated(grande_entreprise)


def test_is_index_egapro_not_updated(grande_entreprise, mocker):
    # Example response from https://egapro.travail.gouv.fr/api/search?q=889297453
    index_egapro_data = """{"data":[],"count":0}"""

    mocker.patch("requests.get", return_value=MockedResponse(index_egapro_data))

    assert not is_index_egapro_updated(grande_entreprise)
