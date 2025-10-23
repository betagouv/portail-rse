import pytest
from django.core.files.base import ContentFile


@pytest.fixture
def analyse(entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    analyse = entreprise.analyses_ia.create(
        fichier=ContentFile("pdf file data", name="fichier.pdf")
    )
    return analyse
