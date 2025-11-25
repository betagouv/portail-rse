from datetime import date

import pytest
from django.core.exceptions import ValidationError

from vsme.models import ANNEE_DEBUT_VSME
from vsme.models import annee_est_valide
from vsme.models import get_annee_rapport_par_defaut
from vsme.models import get_annees_valides
from vsme.models import RapportVSME
from vsme.models import validate_annee_rapport


def test_get_annee_rapport_par_defaut():
    annee_attendue = date.today().year - 1
    assert get_annee_rapport_par_defaut() == annee_attendue


def test_get_annees_valides():
    annees = get_annees_valides()
    annee_max = get_annee_rapport_par_defaut()

    assert annees[0] == ANNEE_DEBUT_VSME
    assert annees[-1] == annee_max
    assert len(annees) == annee_max - ANNEE_DEBUT_VSME + 1


@pytest.mark.parametrize(
    "annee,attendu",
    [
        (2020, True),  # Première année VSME
        (2021, True),
        (2022, True),
        (2023, True),
        (2024, True),
        (date.today().year - 1, True),  # Année par défaut (N-1)
        (date.today().year, False),  # Année courante (N) - invalide
        (date.today().year + 1, False),  # Année future (N+1) - invalide
        (2019, False),  # Avant le début VSME - invalide
        (2018, False),
        (2010, False),
    ],
)
def test_annee_est_valide(annee, attendu):
    assert annee_est_valide(annee) == attendu


@pytest.mark.parametrize(
    "annee",
    [2020, 2021, 2022, 2023, 2024],
)
def test_validate_annee_rapport_valide(annee):
    # Si l'année est valide (entre 2020 et N-1)
    if annee <= get_annee_rapport_par_defaut():
        validate_annee_rapport(annee)


@pytest.mark.parametrize(
    "annee",
    [
        date.today().year,  # Année courante
        date.today().year + 1,  # Année future
        2019,  # Avant 2020
        2018,
        2010,
    ],
)
def test_validate_annee_rapport_invalide(annee):
    with pytest.raises(ValidationError) as ex:
        validate_annee_rapport(annee)
    assert "doit être entre" in str(ex.value)


@pytest.mark.parametrize("annee", [2020, 2021, 2022, 2023, 2024])
def test_creation_rapport_annee_valide(entreprise_factory, alice, annee):
    entreprise = entreprise_factory(utilisateur=alice)

    # Vérifier que l'année est dans la plage valide
    if annee <= get_annee_rapport_par_defaut():
        rapport = RapportVSME.objects.create(entreprise=entreprise, annee=annee)
        rapport.full_clean()
        assert rapport.annee == annee


@pytest.mark.parametrize(
    "annee",
    [
        date.today().year,  # Année courante
        date.today().year + 1,  # Année future
        2019,  # Avant 2020
        2018,
        2010,
    ],
)
def test_creation_rapport_annee_invalide(entreprise_factory, alice, annee):
    entreprise = entreprise_factory(utilisateur=alice)

    rapport = RapportVSME(entreprise=entreprise, annee=annee)
    with pytest.raises(ValidationError):
        rapport.full_clean()


def test_unicite_rapport_par_annee(entreprise_factory, alice):
    from django.db import IntegrityError

    entreprise = entreprise_factory(utilisateur=alice)
    annee = get_annee_rapport_par_defaut()

    RapportVSME.objects.create(entreprise=entreprise, annee=annee)

    # Tentative de créer un second rapport pour la même année
    with pytest.raises(IntegrityError):
        RapportVSME.objects.create(entreprise=entreprise, annee=annee)


def test_plusieurs_rapports_annees_differentes(entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)

    rapport_2024 = RapportVSME.objects.create(entreprise=entreprise, annee=2024)
    rapport_2023 = RapportVSME.objects.create(entreprise=entreprise, annee=2023)
    rapport_2020 = RapportVSME.objects.create(entreprise=entreprise, annee=2020)

    assert rapport_2024.annee == 2024
    assert rapport_2023.annee == 2023
    assert rapport_2020.annee == 2020
    assert entreprise.rapports_vsme.count() == 3
