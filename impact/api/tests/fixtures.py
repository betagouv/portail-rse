import pytest

from entreprises.models import CaracteristiquesAnnuelles


@pytest.fixture
def mock_api_recherche_entreprises(mocker):
    return mocker.patch(
        "api.recherche_entreprises.recherche",
        return_value={
            "siren": "000000001",
            "denomination": "Entreprise SAS",
            "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        },
    )


@pytest.fixture
def mock_api_index_egapro(mocker):
    mocker.patch("api.egapro.indicateurs")
    return mocker.patch("api.egapro.is_index_egapro_published")
