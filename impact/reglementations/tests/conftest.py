import pytest

from entreprises.models import Entreprise
from habilitations.models import add_entreprise_to_user
from reglementations.models import BDESE_50_300, BDESE_300


@pytest.fixture
def bdese_factory(entreprise_factory):
    def create_bdese(
        bdese_class=BDESE_300,
        entreprise=None,
        user=None,
    ):
        if not entreprise:
            entreprise = entreprise_factory(
                effectif="moyen" if bdese_class == BDESE_50_300 else "grand"
            )
        if not user:
            bdese = bdese_class.officials.create(entreprise=entreprise, annee=2021)
        else:
            add_entreprise_to_user(entreprise, user, "Président·e")
            bdese = bdese_class.personals.create(
                entreprise=entreprise, annee=2021, user=user
            )
        return bdese

    return create_bdese


@pytest.fixture(params=[BDESE_50_300, BDESE_300])
def bdese(request, bdese_factory):
    return bdese_factory(request.param)


@pytest.fixture
def grande_entreprise(entreprise_factory):
    return entreprise_factory(effectif="grand")


@pytest.fixture(autouse=True)
def mock_index_egapro(mocker):
    mocker.patch("reglementations.views.get_bdese_data_from_egapro")
    return mocker.patch("reglementations.views.is_index_egapro_updated")
