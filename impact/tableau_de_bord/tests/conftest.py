import pytest


# Empêche tous les tests de faire des appels api
@pytest.fixture(autouse=True)
def mock_api(mock_api_infos_entreprise, mock_api_egapro, mock_api_bges):
    pass
