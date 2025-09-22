import pytest

from vsme.models import RapportVSME


@pytest.fixture
def entreprise_qualifiee(entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    return entreprise


@pytest.fixture
def rapport_vsme(entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    rapport_vsme = RapportVSME.objects.create(entreprise=entreprise, annee=2024)
    return rapport_vsme
