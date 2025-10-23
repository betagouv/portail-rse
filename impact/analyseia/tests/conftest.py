import pytest
from django.core.files.base import ContentFile

from analyseia.models import AnalyseIA
from reglementations.tests.conftest import csrd  # noqa


@pytest.fixture
def analyse(entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    analyse = entreprise.analyses_ia.create(
        fichier=ContentFile("pdf file data", name="fichier.pdf")
    )
    return analyse

@pytest.fixture
def analyse_avec_csrd(csrd):
    document = AnalyseIA.objects.create(
        fichier=ContentFile("pdf file data", name="fichier.pdf")
    )

    document.rapports_csrd.add(csrd)
    return document
