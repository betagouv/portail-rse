import pytest
from django.core.exceptions import ObjectDoesNotExist

from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from habilitations.models import get_habilitation
from reglementations.models.bdese import BDESE_300
from reglementations.models.bdese import BDESE_50_300
from reglementations.models.bdese import BDESEAvecAccord


# Empêche tous les tests de faire des appels api
@pytest.fixture(autouse=True)
def mock_api(mock_api_recherche_entreprises, mock_api_egapro, mock_api_bges):
    pass


@pytest.fixture
def bdese_factory(entreprise_factory, date_cloture_dernier_exercice):
    def create_bdese(
        bdese_class=BDESE_300,
        entreprise=None,
        user=None,
        annee=date_cloture_dernier_exercice.year,
    ):
        if not entreprise:
            entreprise = entreprise_factory(
                effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
                if bdese_class == BDESE_50_300
                else CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499
            )
        if not user:
            bdese = bdese_class.officials.create(entreprise=entreprise, annee=annee)
        else:
            try:
                get_habilitation(user, entreprise)
            except ObjectDoesNotExist:
                attach_user_to_entreprise(user, entreprise, "Président·e")
            bdese = bdese_class.personals.create(
                entreprise=entreprise, annee=annee, user=user
            )
        return bdese

    return create_bdese


@pytest.fixture(params=[BDESE_50_300, BDESE_300])
def bdese(request, bdese_factory):
    return bdese_factory(request.param)


@pytest.fixture
def bdese_avec_accord(bdese_factory, entreprise_factory, alice):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499, bdese_accord=True
    )
    return bdese_factory(bdese_class=BDESEAvecAccord, entreprise=entreprise, user=alice)


@pytest.fixture
def grande_entreprise(entreprise_factory):
    return entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499
    )


@pytest.fixture
def habilitated_user(bdese, alice):
    attach_user_to_entreprise(alice, bdese.entreprise, "Présidente")
    habilitation = get_habilitation(alice, bdese.entreprise)
    habilitation.confirm()
    habilitation.save()
    return alice


@pytest.fixture
def not_habilitated_user(bdese, bob):
    attach_user_to_entreprise(bob, bdese.entreprise, "Testeur")
    return bob
