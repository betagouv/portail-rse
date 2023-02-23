import pytest

from entreprises.models import Entreprise

@pytest.fixture
def alice(django_user_model):
    alice = django_user_model.objects.create(email="alice@impact.test")
    return alice

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