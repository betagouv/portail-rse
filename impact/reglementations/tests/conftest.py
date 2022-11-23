import pytest

from entreprises.models import Entreprise
from reglementations.models import BDESE_50_300, BDESE_300


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
def bdese_factory(entreprise_factory):
    def create_bdese(
        bdese_class=BDESE_300,
        entreprise=None,
    ):
        if not entreprise:
            entreprise = entreprise_factory(
                effectif="moyen" if bdese_class == BDESE_50_300 else "grand"
            )
        bdese = bdese_class.objects.create(entreprise=entreprise)
        return bdese

    return create_bdese


@pytest.fixture
def grande_entreprise(entreprise_factory):
    return entreprise_factory(effectif="grand")


@pytest.fixture(autouse=True)
def mock_index_egapro(mocker):
    mocker.patch("reglementations.views.get_bdese_data_from_index_egapro")
    return mocker.patch("reglementations.views.is_index_egapro_updated")
