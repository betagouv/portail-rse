import pytest

from entreprises.models import CaracteristiquesAnnuelles

JETON = "jeton-de-test"


@pytest.fixture
def poc_actif(settings):
    settings.POC_LEE_TOKEN = JETON
    settings.DEBUG = True


@pytest.fixture
def sans_reseau(mocker):
    mocker.patch("requests.get", side_effect=AssertionError("appel réseau"))
    mocker.patch("requests.post", side_effect=AssertionError("appel réseau"))


@pytest.fixture
def pme_transport(entreprise_factory):
    return entreprise_factory(
        identifiant="095680393",
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        effectif_securite_sociale=CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_ENTRE_50_ET_249,
    )


@pytest.fixture
def tpe_commerce(entreprise_factory):
    return entreprise_factory(identifiant="045850617")
