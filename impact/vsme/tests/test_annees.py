from datetime import date

import pytest
from django.core.exceptions import ValidationError

from vsme.models import ANNEE_DEBUT_VSME
from vsme.models import annee_est_valide
from vsme.models import get_annee_dernier_exercice_clos
from vsme.models import get_annee_max_valide
from vsme.models import get_annee_rapport_par_defaut
from vsme.models import get_annees_valides
from vsme.models import RapportVSME
from vsme.models import validate_annee_rapport


# Tests sans entreprise (comportement par défaut : N-1 calendaire)


def test_get_annee_rapport_par_defaut_sans_entreprise():
    """Sans entreprise, l'année par défaut est N-1 calendaire"""
    annee_attendue = date.today().year - 1
    assert get_annee_rapport_par_defaut() == annee_attendue


def test_get_annee_max_valide_sans_entreprise():
    """Sans entreprise, l'année max est N calendaire"""
    annee_attendue = date.today().year
    assert get_annee_max_valide() == annee_attendue


def test_get_annees_valides_sans_entreprise():
    annees = get_annees_valides()
    annee_max = get_annee_max_valide()

    assert annees[0] == ANNEE_DEBUT_VSME
    assert annees[-1] == annee_max
    assert len(annees) == annee_max - ANNEE_DEBUT_VSME + 1


# Tests avec entreprise et différentes dates de clôture


def test_get_annee_dernier_exercice_clos_entreprise_sans_date_cloture(
    entreprise_factory, alice
):
    """Une entreprise sans date de clôture utilise N-1 par défaut"""
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = None
    entreprise.save()

    assert get_annee_dernier_exercice_clos(entreprise) == date.today().year - 1


def test_get_annee_dernier_exercice_clos_cloture_31_decembre(entreprise_factory, alice):
    """
    Entreprise avec clôture au 31/12 :
    - Avant le 31/12 de l'année N, le dernier exercice clos est N-1
    - Après le 31/12 de l'année N, le dernier exercice clos est N
    """
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 12, 31)
    entreprise.save()

    # Aujourd'hui on est le 12 décembre 2025, donc avant la clôture du 31/12/2025
    # Le dernier exercice clos est donc 2024
    assert get_annee_dernier_exercice_clos(entreprise) == date.today().year - 1


def test_get_annee_dernier_exercice_clos_cloture_30_juin(entreprise_factory, alice):
    """
    Entreprise avec clôture au 30/06 :
    - Après le 30/06 de l'année N, le dernier exercice clos est N
    - Avant le 30/06 de l'année N, le dernier exercice clos est N-1
    """
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 6, 30)
    entreprise.save()

    # Aujourd'hui on est le 12 décembre 2025, donc après la clôture du 30/06/2025
    # Le dernier exercice clos est donc 2025
    assert get_annee_dernier_exercice_clos(entreprise) == date.today().year


def test_get_annee_rapport_par_defaut_avec_entreprise_cloture_31_decembre(
    entreprise_factory, alice
):
    """Avec une clôture au 31/12, l'année par défaut est le dernier exercice clos"""
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 12, 31)
    entreprise.save()

    # Le dernier exercice clos est N-1 (clôture 31/12 pas encore passée)
    assert get_annee_rapport_par_defaut(entreprise) == date.today().year - 1


def test_get_annee_rapport_par_defaut_avec_entreprise_cloture_30_juin(
    entreprise_factory, alice
):
    """Avec une clôture au 30/06, l'année par défaut est le dernier exercice clos"""
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 6, 30)
    entreprise.save()

    # Le dernier exercice clos est N (clôture 30/06 déjà passée)
    assert get_annee_rapport_par_defaut(entreprise) == date.today().year


def test_get_annee_max_valide_avec_entreprise_cloture_31_decembre(
    entreprise_factory, alice
):
    """L'année max est dernier exercice clos + 1 (permettant de préparer l'exercice en cours)"""
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 12, 31)
    entreprise.save()

    # Dernier exercice clos = N-1, donc max = N
    assert get_annee_max_valide(entreprise) == date.today().year


def test_get_annee_max_valide_avec_entreprise_cloture_30_juin(
    entreprise_factory, alice
):
    """L'année max est dernier exercice clos + 1"""
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 6, 30)
    entreprise.save()

    # Dernier exercice clos = N, donc max = N+1
    assert get_annee_max_valide(entreprise) == date.today().year + 1


def test_get_annees_valides_avec_entreprise(entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 6, 30)
    entreprise.save()

    annees = get_annees_valides(entreprise)
    annee_max = get_annee_max_valide(entreprise)

    assert annees[0] == ANNEE_DEBUT_VSME
    assert annees[-1] == annee_max
    assert date.today().year + 1 in annees  # N+1 est disponible pour clôture 30/06


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


def test_annee_est_valide_avec_entreprise_cloture_30_juin(entreprise_factory, alice):
    """Avec clôture 30/06, les années valides vont de 2020 à N+1"""
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 6, 30)
    entreprise.save()

    assert annee_est_valide(2020, entreprise)
    assert annee_est_valide(date.today().year, entreprise)
    assert annee_est_valide(date.today().year + 1, entreprise)  # N+1 est valide
    assert not annee_est_valide(date.today().year + 2, entreprise)  # N+2 invalide
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
