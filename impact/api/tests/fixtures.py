import pytest

from entreprises.models import CaracteristiquesAnnuelles


@pytest.fixture
def mock_api_recherche_entreprises(mocker):
    return mocker.patch(
        "api.recherche_entreprises.recherche",
        return_value={
            "siren": "000000001",
            "denomination": "Entreprise SAS",
            "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
            "categorie_juridique_sirene": 5710,
            "code_pays_etranger_sirene": None,
        },
    )


@pytest.fixture
def mock_api_egapro(mocker):
    mocker.patch("api.egapro.indicateurs_bdese")
    return mocker.patch("api.egapro.is_index_egapro_published")


@pytest.fixture
def mock_api_bges(mocker):
    return mocker.patch("api.bges.last_reporting_year")
