from datetime import date

import pytest
from django.core.exceptions import ValidationError
from freezegun import freeze_time

from vsme.models import ANNEE_DEBUT_VSME
from vsme.models import annee_est_valide
from vsme.models import get_annees_valides
from vsme.models import RapportVSME
from vsme.models import validate_annee_rapport


@freeze_time("2025-12-12")
def test_get_annees_valides_avec_entreprise(entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 6, 30)
    entreprise.save()

    annees = get_annees_valides(entreprise)

    assert annees[0] == ANNEE_DEBUT_VSME
    assert annees[-1] == 2026  # (N+1) est disponible pour clôture 30/06


def test_annee_est_valide_avec_entreprise_cloture_31_decembre(
    entreprise_factory, alice
):
    """Avec clôture 31/12, les années valides vont de 2020 à N"""
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 12, 31)
    entreprise.save()

    assert annee_est_valide(2020, entreprise)
    assert annee_est_valide(date.today().year - 1, entreprise)
    assert annee_est_valide(date.today().year, entreprise)  # N est valide
    assert not annee_est_valide(date.today().year + 1, entreprise)  # N+1 invalide
    assert not annee_est_valide(2019, entreprise)


@freeze_time("2025-12-12")
def test_annee_est_valide_avec_entreprise_cloture_30_juin(entreprise_factory, alice):
    """Avec clôture 30/06, les années valides vont de 2020 à N+1"""
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 6, 30)
    entreprise.save()

    assert annee_est_valide(2020, entreprise)
    assert annee_est_valide(2025, entreprise)  # N=2025 est valide
    assert annee_est_valide(2026, entreprise)  # N+1=2026 est valide
    assert not annee_est_valide(2027, entreprise)  # N+2=2027 invalide
    assert not annee_est_valide(2019, entreprise)


# Tests du validateur de modèle (sans contexte d'entreprise)


@pytest.mark.parametrize(
    "annee",
    [2020, 2021, 2022, 2023, 2024, 2025, date.today().year + 1],
)
def test_validate_annee_rapport_valide(annee):
    """Le validateur accepte les années entre 2020 et N+1 calendaire"""
    # Ne doit pas lever d'exception
    validate_annee_rapport(annee)


@pytest.mark.parametrize(
    "annee",
    [
        date.today().year + 2,  # Année future (N+2)
        2019,  # Avant 2020
        2018,
        2010,
    ],
)
def test_validate_annee_rapport_invalide(annee):
    with pytest.raises(ValidationError) as ex:
        validate_annee_rapport(annee)
    assert "doit être entre" in str(ex.value)


# Tests de création de rapport


@pytest.mark.parametrize("annee", [2020, 2021, 2022, 2023, 2024, 2025])
def test_creation_rapport_annee_valide(entreprise_factory, alice, annee):
    entreprise = entreprise_factory(utilisateur=alice)
    rapport = RapportVSME.objects.create(entreprise=entreprise, annee=annee)
    rapport.full_clean()
    assert rapport.annee == annee


@pytest.mark.parametrize(
    "annee",
    [
        date.today().year + 2,  # Année future (N+2)
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
    annee = 2024

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
