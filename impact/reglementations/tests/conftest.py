import pytest

from entreprises.models import Entreprise


@pytest.fixture
def entreprise_factory(db):
    def create_entreprise(
        siren="000000001",
        effectif="petit",
        bdese_accord=False,
        raison_sociale="Entreprise SAS",
    ):
        entreprise = Entreprise.objects.create(
            siren=siren,
            effectif=effectif,
            bdese_accord=bdese_accord,
            raison_sociale=raison_sociale,
        )
        return entreprise

    return create_entreprise


@pytest.fixture
def entreprise(entreprise_factory):
    return entreprise_factory()


@pytest.fixture(autouse=True)
def mock_index_egapro(mocker):
    mocker.patch("reglementations.views.get_bdese_data_from_index_egapro")
    return mocker.patch("reglementations.views.is_index_egapro_updated")
