import pytest


@pytest.fixture
def mock_api_recherche_entreprise(mocker):
    return mocker.patch(
        "api.recherche_entreprises.recherche",
        return_value={
            "siren": "000000001",
            "raison_sociale": "Entreprise SAS",
            "effectif": "petit",
        },
    )
