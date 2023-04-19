import pytest

from entreprises.models import Entreprise


@pytest.fixture
def alice(django_user_model):
    alice = django_user_model.objects.create(
        prenom="Alice",
        nom="Cooper",
        email="alice@impact.test",
        reception_actualites=False,
    )
    return alice


@pytest.fixture
def bob(django_user_model):
    bob = django_user_model.objects.create(
        prenom="Bob",
        nom="Dylan",
        email="bob@impact.test",
        reception_actualites=False,
    )
    return bob


@pytest.fixture
def entreprise_factory(db):
    def create_entreprise(
        siren="000000001",
        effectif=Entreprise.EFFECTIF_MOINS_DE_50,
        bdese_accord=False,
        denomination="Entreprise SAS",
    ):
        entreprise = Entreprise.objects.create(
            siren=siren,
            effectif=effectif,
            bdese_accord=bdese_accord,
            denomination=denomination,
        )
        return entreprise

    return create_entreprise
