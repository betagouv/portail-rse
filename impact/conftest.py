import pytest

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise


@pytest.fixture
def alice(django_user_model):
    alice = django_user_model.objects.create(
        prenom="Alice",
        nom="Cooper",
        email="alice@impact.test",
        reception_actualites=False,
        is_email_confirmed=True,
    )
    return alice


@pytest.fixture
def bob(django_user_model):
    bob = django_user_model.objects.create(
        prenom="Bob",
        nom="Dylan",
        email="bob@impact.test",
        reception_actualites=False,
        is_email_confirmed=True,
    )
    return bob


@pytest.fixture
def entreprise_factory(db):
    def create_entreprise(
        siren="000000001",
        denomination="Entreprise SAS",
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        bdese_accord=False,
    ):
        entreprise = Entreprise.objects.create(
            siren=siren,
            denomination=denomination,
        )
        caracteristiques = entreprise.actualise_caracteristiques(
            effectif=effectif,
            bdese_accord=bdese_accord,
        )
        caracteristiques.save()
        return entreprise

    return create_entreprise
