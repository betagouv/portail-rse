import pytest

from entreprises.models import Evolution


@pytest.fixture
def mock_api_recherche_entreprises(mocker):
    return mocker.patch(
        "api.recherche_entreprises.recherche",
        return_value={
            "siren": "000000001",
            "denomination": "Entreprise SAS",
            "effectif": Evolution.EFFECTIF_MOINS_DE_50,
        },
    )
