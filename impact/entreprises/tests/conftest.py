import pytest

from entreprises.models import Entreprise


@pytest.fixture
def entreprise_non_qualifiee(alice):
    entreprise = Entreprise.objects.create(
        siren="000000001", denomination="Entreprise SAS"
    )
    return entreprise
