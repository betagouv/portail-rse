import pytest

from api.exceptions import APIError
from api.exceptions import SirenError
from api.infos_entreprise import infos_entreprise
from api.tests.fixtures import mock_api_recherche_entreprises  # noqa
from api.tests.fixtures import mock_api_sirene  # noqa
from entreprises.models import CaracteristiquesAnnuelles

SIREN = "123456789"


def test_infos_entreprise_succes_api_recherche_entreprises(
    mock_api_recherche_entreprises, mock_api_sirene
):
    mock_api_recherche_entreprises.return_value = {
        "siren": SIREN,
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": None,
    }
    infos = infos_entreprise(SIREN)

    mock_api_recherche_entreprises.assert_called_once_with(SIREN)
    assert not mock_api_sirene.called
    assert infos == {
        "siren": SIREN,
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": None,
    }


def test_infos_entreprise_echec_api_recherche_entreprises_erreur_de_l_api_puis_succes_api_sirene(
    mock_api_recherche_entreprises, mock_api_sirene
):
    mock_api_recherche_entreprises.side_effect = APIError
    mock_api_sirene.return_value = {
        "siren": SIREN,
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": None,
    }
    infos = infos_entreprise(SIREN)

    mock_api_recherche_entreprises.assert_called_once_with(SIREN)
    mock_api_sirene.assert_called_once_with(SIREN)
    assert infos == {
        "siren": SIREN,
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": None,
    }


def test_infos_entreprise_echec_api_recherche_entreprises_siren_invalide(
    mock_api_recherche_entreprises, mock_api_sirene
):
    mock_api_recherche_entreprises.side_effect = SirenError("Message d'erreur")

    with pytest.raises(SirenError) as e:
        infos_entreprise(SIREN)

    mock_api_recherche_entreprises.assert_called_once_with(SIREN)
    assert not mock_api_sirene.called
    assert str(e.value) == "Message d'erreur"


def test_infos_entreprise_echec_api_recherche_entreprises_et_api_sirene(
    mock_api_recherche_entreprises, mock_api_sirene
):
    mock_api_recherche_entreprises.side_effect = APIError(
        "Message d'erreur recherche entreprises"
    )
    mock_api_sirene.side_effect = APIError("Message d'erreur sirene")

    with pytest.raises(APIError) as e:
        infos_entreprise(SIREN)

    mock_api_recherche_entreprises.assert_called_once_with(SIREN)
    mock_api_sirene.assert_called_once_with(SIREN)
    assert str(e.value) == "Message d'erreur sirene"
