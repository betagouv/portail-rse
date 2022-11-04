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
