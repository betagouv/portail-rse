import pytest
from django.core.files.base import ContentFile

from analyseia.models import AnalyseIA
from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import Habilitation
from reglementations.models import BDESE_300
from reglementations.models import BDESE_50_300
from reglementations.models import BDESEAvecAccord


# Empêche tous les tests de faire des appels api
@pytest.fixture(autouse=True)
def mock_api(mock_api_infos_entreprise, mock_api_egapro, mock_api_bges):
    pass


@pytest.fixture(params=[BDESE_50_300, BDESE_300])
def bdese(request, bdese_factory):
    return bdese_factory(request.param)


@pytest.fixture
def bdese_avec_accord(bdese_factory):
    return bdese_factory(bdese_class=BDESEAvecAccord)


@pytest.fixture
def document(csrd):
    document = AnalyseIA.objects.create(
        fichier=ContentFile("pdf file data", name="fichier.pdf")
    )

    document.rapports_csrd.add(csrd)
    return document


@pytest.fixture
def grande_entreprise(entreprise_factory):
    return entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499
    )


@pytest.fixture
def habilitated_user(bdese, alice):
    Habilitation.ajouter(bdese.entreprise, alice, fonctions="Présidente")
    habilitation = Habilitation.pour(bdese.entreprise, alice)
    habilitation.save()
    return alice


@pytest.fixture
def not_habilitated_user(bdese, bob):
    Habilitation.ajouter(bdese.entreprise, bob, fonctions="Testeur")
    return bob
