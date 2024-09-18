import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.utils import IntegrityError
from freezegun import freeze_time

from habilitations.models import get_habilitation
from reglementations.models.bdese import annees_a_remplir_bdese
from reglementations.models.bdese import BDESE_300
from reglementations.models.bdese import BDESE_50_300
from reglementations.models.bdese import BDESEAvecAccord
from reglementations.models.bdese import BDESEError
from reglementations.models.bdese import CategoryField
from reglementations.models.bdese import CategoryType
from reglementations.models.bdese import derniere_annee_a_remplir_bdese


def test_category_field_with_hard_coded_categories():
    def category_field_default():
        return {"catégorie 1": "yolo", "catégorie 2": "yolo2"}

    category_field = CategoryField(
        base_field=models.BooleanField,
        categories=["catégorie 1", "catégorie 2"],
        default=category_field_default,
    )

    name, path, args, kwargs = category_field.deconstruct()
    new_category_field = CategoryField(*args, **kwargs)

    assert (
        new_category_field.base_field
        == category_field.base_field
        == models.BooleanField
    )
    assert (
        new_category_field.category_type
        == category_field.category_type
        == CategoryType.HARD_CODED
    )
    assert (
        new_category_field.categories
        == category_field.categories
        == ["catégorie 1", "catégorie 2"]
    )


def test_category_field_with_category_type():
    category_field = CategoryField(
        base_field=models.BooleanField,
        category_type=CategoryType.PROFESSIONNELLE,
    )

    name, path, args, kwargs = category_field.deconstruct()
    new_category_field = CategoryField(*args, **kwargs)

    assert (
        new_category_field.base_field
        == category_field.base_field
        == models.BooleanField
    )
    assert (
        new_category_field.category_type
        == category_field.category_type
        == CategoryType.PROFESSIONNELLE
    )
    assert new_category_field.categories == category_field.categories is None


@pytest.mark.django_db(transaction=True)
def test_bdese_300(grande_entreprise):
    with pytest.raises(IntegrityError):
        BDESE_300.objects.create()

    bdese = BDESE_300.objects.create(entreprise=grande_entreprise, annee=2022)

    assert bdese.created_at
    assert bdese.updated_at
    assert bdese.annee == 2022
    assert bdese.entreprise == grande_entreprise
    assert "effectif_total" in bdese.category_fields()
    assert bdese.effectif_total is None
    assert "nombre_travailleurs_exterieurs" not in bdese.category_fields()
    assert bdese.nombre_travailleurs_exterieurs is None

    assert not bdese.is_configured
    assert not bdese.is_complete
    for step in bdese.STEPS:
        assert not bdese.step_is_complete(step)
    with pytest.raises(KeyError):
        assert not bdese.step_is_complete(len(bdese.STEPS) + 1)

    for step in bdese.STEPS:
        bdese.mark_step_as_complete(step)
        assert bdese.step_is_complete(step)

        bdese.mark_step_as_incomplete(step)
        assert not bdese.step_is_complete(step)

        bdese.mark_step_as_complete(step)
    assert bdese.is_complete

    bdese.categories_professionnelles = ["categorie 1", "categorie 2", "categorie 3"]
    bdese.categories_professionnelles_detaillees = [
        "categorie 1",
        "categorie 2",
        "categorie 3",
        "categorie 4",
        "categorie 5",
    ]
    bdese.niveaux_hierarchiques = ["niveau 1", "niveau 2"]
    assert bdese.is_configured


@pytest.mark.django_db(transaction=True)
def test_bdese_50_300(grande_entreprise):
    with pytest.raises(IntegrityError):
        BDESE_50_300.objects.create()

    bdese = BDESE_50_300.objects.create(entreprise=grande_entreprise, annee=2022)

    assert bdese.created_at
    assert bdese.updated_at
    assert bdese.annee == 2022
    assert bdese.entreprise == grande_entreprise
    assert "effectif_mensuel" in bdese.category_fields()
    assert bdese.effectif_mensuel is None
    assert "effectif_cdi" not in bdese.category_fields()
    assert bdese.effectif_cdi is None

    assert not bdese.is_configured
    assert not bdese.is_complete
    for step in bdese.STEPS:
        assert not bdese.step_is_complete(step)
    with pytest.raises(KeyError):
        assert not bdese.step_is_complete(len(bdese.STEPS) + 1)

    for step in bdese.STEPS:
        bdese.mark_step_as_complete(step)
        assert bdese.step_is_complete(step)

        bdese.mark_step_as_incomplete(step)
        assert not bdese.step_is_complete(step)

        bdese.mark_step_as_complete(step)
    assert bdese.is_complete

    bdese.categories_professionnelles = ["categorie 1", "categorie 2", "categorie 3"]
    assert bdese.is_configured


@pytest.mark.django_db(transaction=True)
def test_bdese_avec_accord(grande_entreprise):
    with pytest.raises(IntegrityError):
        BDESEAvecAccord.objects.create()

    bdese = BDESEAvecAccord.objects.create(entreprise=grande_entreprise, annee=2022)

    assert bdese.created_at
    assert bdese.updated_at
    assert bdese.annee == 2022
    assert bdese.entreprise == grande_entreprise
    assert not bdese.is_complete

    assert not bdese.is_complete
    bdese.toggle_completion()
    assert bdese.is_complete

    bdese.toggle_completion()
    assert not bdese.is_complete

    with pytest.raises(BDESEError):
        bdese.mark_step_as_complete(0)
    with pytest.raises(BDESEError):
        bdese.mark_step_as_incomplete(0)
    with pytest.raises(BDESEError):
        bdese.step_is_complete(0)


def test_derniere_annee_a_remplir_bdese():
    with freeze_time("2022-11-23"):
        annee = derniere_annee_a_remplir_bdese()
        assert annee == 2021

    with freeze_time("2023-11-23"):
        annee = derniere_annee_a_remplir_bdese()
        assert annee == 2022


def test_annees_a_remplir_pour_bdese():
    with freeze_time("2022-11-23"):
        annees = annees_a_remplir_bdese()
        assert annees == [2019, 2020, 2021, 2022, 2023, 2024]

    with freeze_time("2023-11-23"):
        annees = annees_a_remplir_bdese()
        assert annees == [2020, 2021, 2022, 2023, 2024, 2025]


def test_personal_bdese_is_copied_to_official_bdese_when_habilitation_is_confirmed(
    client, alice, bdese_factory
):
    bdese = bdese_factory(user=alice)
    CATEGORIES_PROFESSIONNELLES = [
        "categorie 1",
        "categorie 2",
        "categorie 3",
        "categorie 4",
    ]
    bdese.categories_professionnelles = CATEGORIES_PROFESSIONNELLES
    bdese.save()
    assert bdese.__class__.personals.get(entreprise=bdese.entreprise)
    with pytest.raises(ObjectDoesNotExist):
        assert bdese.__class__.officials.get(entreprise=bdese.entreprise)

    habilitation = get_habilitation(alice, bdese.entreprise)
    habilitation.confirm()

    assert bdese.__class__.personals.get(entreprise=bdese.entreprise)
    official_bdese = bdese.__class__.officials.get(entreprise=bdese.entreprise)
    assert official_bdese.categories_professionnelles == CATEGORIES_PROFESSIONNELLES


def test_personal_bdese_is_not_copied_to_official_bdese_if_already_exists(
    client, alice, bdese_factory, grande_entreprise
):
    official_bdese = bdese_factory(entreprise=grande_entreprise)
    personal_bdese = bdese_factory(entreprise=grande_entreprise, user=alice)
    CATEGORIES_PROFESSIONNELLES = [
        "categorie 1",
        "categorie 2",
        "categorie 3",
        "categorie 4",
    ]
    personal_bdese.categories_professionnelles = CATEGORIES_PROFESSIONNELLES
    personal_bdese.save()

    habilitation = get_habilitation(alice, grande_entreprise)
    habilitation.confirm()

    official_bdese = official_bdese.__class__.officials.get(
        entreprise=grande_entreprise
    )
    assert official_bdese.categories_professionnelles != CATEGORIES_PROFESSIONNELLES


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("bdese_class", [BDESEAvecAccord, BDESE_50_300, BDESE_300])
def test_unique_yearly_bdese_with_user(bdese_class, alice, grande_entreprise):
    bdese_class.objects.create(entreprise=grande_entreprise, user=alice, annee=2022)
    bdese_class.objects.create(entreprise=grande_entreprise, annee=2022)

    with pytest.raises(IntegrityError):
        bdese_class.objects.create(entreprise=grande_entreprise, user=alice, annee=2022)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("bdese_class", [BDESEAvecAccord, BDESE_50_300, BDESE_300])
def test_unique_yearly_bdese_without_user(bdese_class, alice, grande_entreprise):
    bdese_class.objects.create(entreprise=grande_entreprise, annee=2022)
    bdese_class.objects.create(entreprise=grande_entreprise, user=alice, annee=2022)

    with pytest.raises(IntegrityError):
        bdese_class.objects.create(entreprise=grande_entreprise, annee=2022)
