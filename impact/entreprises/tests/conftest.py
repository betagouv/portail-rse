import pytest

from entreprises.models import Entreprise


@pytest.fixture
def unqualified_entreprise(alice):
    entreprise = Entreprise.objects.create(
        siren="00000001", raison_sociale="Entreprise SAS"
    )
    return entreprise
