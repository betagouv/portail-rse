from datetime import date

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile

from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import Habilitation
from reglementations.models import BDESE_300
from reglementations.models import BDESE_50_300
from reglementations.models import BDESEAvecAccord
from reglementations.models import RapportCSRD
from reglementations.models.csrd import DocumentAnalyseIA

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
                Habilitation.pour(entreprise, user)
            except ObjectDoesNotExist:
                Habilitation.ajouter(entreprise, user, fonctions="Président·e")
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
def csrd(entreprise_factory, alice):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    csrd = RapportCSRD.objects.create(
        entreprise=entreprise,
        proprietaire=alice,
        annee=date.today().year,
    )
    return csrd


@pytest.fixture
def document(csrd):
    document = DocumentAnalyseIA.objects.create(
        rapport_csrd=csrd, fichier=ContentFile("pdf file data", name="fichier.pdf")
    )
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
    habilitation.confirm()
    habilitation.save()
    return alice


@pytest.fixture
def not_habilitated_user(bdese, bob):
    Habilitation.ajouter(bdese.entreprise, bob, fonctions="Testeur")
    return bob
