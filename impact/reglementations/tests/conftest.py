import pytest

from entreprises.models import Entreprise


@pytest.fixture
def entreprise(db):
    entreprise = Entreprise.objects.create(
        siren="000000001",
        effectif="petit",
        bdese_accord=False,
        raison_sociale="Entreprise SAS",
    )
    return entreprise


@pytest.fixture(autouse=True)
def mock_index_egapro(mocker):
    return mocker.patch("reglementations.views.is_index_egapro_updated")
