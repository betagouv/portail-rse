from datetime import date

from freezegun import freeze_time

from entreprises.models import Exercice
from entreprises.models import get_dernier_exercice_clos


@freeze_time("2026-04-17")
def test_exercices_pour_une_entreprise_sans_date_cloture(entreprise_factory):
    """Une entreprise sans date de clôture utilise l'année civile"""
    entreprise = entreprise_factory()
    entreprise.date_cloture_exercice = None
    entreprise.save()

    assert get_dernier_exercice_clos(entreprise) == Exercice(date(2025, 1, 1))
    assert entreprise.exercice_en_cours == Exercice(date(2026, 1, 1))


@freeze_time("2026-04-17")
def test_exercices_pour_une_entreprise_qui_cloture_la_veille(entreprise_factory):
    entreprise = entreprise_factory(date_cloture_exercice=date(2023, 4, 16))

    assert get_dernier_exercice_clos(entreprise) == Exercice(
        date_ouverture=date(2025, 4, 17)
    )
    assert entreprise.exercice_en_cours == Exercice(date(2026, 4, 17))


@freeze_time("2025-12-12")
def test_exercices_cloture_31_decembre(entreprise_factory):
    """
    Entreprise avec clôture au 31/12, le dernier exercice clos est N-1
    """
    entreprise = entreprise_factory(date_cloture_exercice=date(2023, 12, 31))

    # Aujourd'hui on est le 12 décembre 2025, donc avant la clôture du 31/12/2025
    # Le dernier exercice clos est donc 2024
    assert get_dernier_exercice_clos(entreprise) == Exercice(
        date_ouverture=date(2024, 1, 1)
    )
    assert entreprise.exercice_en_cours == Exercice(date(2025, 1, 1))


def test_exercices_cloture_30_juin(entreprise_factory):
    """
    Entreprise avec clôture au 30/06 :
    - Après le 30/06 de l'année N, le dernier exercice clos est N
    - Avant le 30/06 de l'année N, le dernier exercice clos est N-1
    """
    entreprise = entreprise_factory(date_cloture_exercice=date(2023, 6, 30))

    # On est le 12 juin 2025, donc avant la clôture du 30/06/2025
    # Le dernier exercice clos est donc 2023-2024
    with freeze_time("2025-06-12"):
        assert get_dernier_exercice_clos(entreprise) == Exercice(
            date_ouverture=date(2023, 7, 1)
        )
        assert entreprise.exercice_en_cours == Exercice(date(2024, 7, 1))

    # On est le 12 décembre 2025, donc après la clôture du 30/06/2025
    # Le dernier exercice clos est donc 2024-2025
    with freeze_time("2025-12-12"):
        assert get_dernier_exercice_clos(entreprise) == Exercice(
            date_ouverture=date(2024, 7, 1)
        )
        assert entreprise.exercice_en_cours == Exercice(date(2025, 7, 1))
