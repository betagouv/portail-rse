import json

from django import forms
import pytest

from reglementations.forms import (
    bdese_form_factory,
    categories_professionnelles_form_factory,
    BDESE_50_300_FIELDS,
    BDESE_300_FIELDS,
    BDESE_50_300_FIELDS,
)
from reglementations.models import BDESE_300, BDESE_50_300


@pytest.fixture
def bdese_300(bdese_factory):
    return bdese_factory(BDESE_300)


@pytest.fixture
def bdese_50_300(bdese_factory):
    return bdese_factory(BDESE_50_300)


@pytest.mark.parametrize("step", range(1, 11))
def test_bdese_form_step_with_new_bdese_300_instance(step, bdese_300):
    categories_professionnelles = ["catégorie 1", "catégorie 2", "catégorie 3"]
    categories_professionnelles_detaillees = [
        "catégorie détaillée 1",
        "catégorie détaillée 2",
        "catégorie détaillée 3",
        "catégorie détaillée 4",
        "catégorie détaillée 5",
    ]
    form = bdese_form_factory(
        bdese_300,
        step,
        categories_professionnelles,
        categories_professionnelles_detaillees,
    )

    assert form.instance == bdese_300
    assert len(form.fields) == len(BDESE_300_FIELDS[step]) + 1
    assert "annee" not in form.fields
    assert "entreprise" not in form.fields
    for field in BDESE_300_FIELDS[step]:
        assert field in form.fields
    assert "indicateurs_externes_in_step" in form.fields

    for field in [
        field for field in form.fields if field in bdese_300.category_fields()
    ]:
        assert isinstance(form.fields[field], forms.MultiValueField)
        assert form.fields[field].categories

    for field in form.fields:
        if field == "unite_absenteisme":
            assert form[field].value() == "J"
        elif field == "remuneration_moyenne_ou_mediane":
            assert form[field].value() == "moyenne"
        elif field == "indicateurs_externes_in_step":
            assert form[field].value() == json.dumps([])
        else:
            assert not form[field].value()

    bound_form = bdese_form_factory(
        bdese_300,
        step,
        categories_professionnelles,
        data={"unite_absenteisme": "J", "remuneration_moyenne_ou_mediane": "moyenne"},
    )

    assert bound_form.is_valid(), bound_form.errors


def test_fields_of_complete_step_are_disabled(bdese):
    bdese.mark_step_as_complete(1)

    form = bdese_form_factory(bdese, 1)

    for field in form.fields:
        assert form.fields[field].disabled


def test_form_is_initialized_with_fetched_data(bdese_300):
    form = bdese_form_factory(bdese_300, 3)

    assert not form["nombre_femmes_plus_hautes_remunerations"].value()

    fetched_data = {"nombre_femmes_plus_hautes_remunerations": 10}
    form = bdese_form_factory(bdese_300, 3, fetched_data=fetched_data)

    assert form["nombre_femmes_plus_hautes_remunerations"].value() == 10


@pytest.mark.parametrize("step", range(1, 11))
def test_indicateurs_externes_in_step_field(step, bdese_300):
    # tente d'ajouter un champ de l'étape en cours dans les indicateurs externes
    # et un champ d'une autre étape qui est ignoré
    field_in_step = BDESE_300_FIELDS[step][0]
    another_step = (step + 1) % len(bdese_300.STEPS)
    field_in_another_step = BDESE_300_FIELDS[another_step][0]

    form = bdese_form_factory(
        bdese_300,
        step,
        data={
            "unite_absenteisme": "J",
            "remuneration_moyenne_ou_mediane": "moyenne",
            "indicateurs_externes_in_step": [field_in_step, field_in_another_step],
        },
    )
    form.save()

    bdese_300.refresh_from_db()
    assert bdese_300.indicateurs_externes == [field_in_step]

    # les indicateurs externes de l'étape sont correctement inialisés
    bdese_300.indicateurs_externes = [field_in_step, field_in_another_step]
    bdese_300.save()

    form = bdese_form_factory(bdese_300, step)

    assert form["indicateurs_externes_in_step"].value() == json.dumps([field_in_step])

    # supprime l'indicateur externe de l'étape
    form = bdese_form_factory(
        bdese_300,
        step,
        data={
            "unite_absenteisme": "J",
            "remuneration_moyenne_ou_mediane": "moyenne",
            "indicateurs_externes_in_step": [],
        },
    )
    form.save()

    bdese_300.refresh_from_db()
    assert bdese_300.indicateurs_externes == [field_in_another_step]


@pytest.mark.parametrize("step", range(1, 11))
def test_bdese_form_with_new_bdese_50_300_instance(step, bdese_50_300):
    categories_professionnelles = ["catégorie 1", "catégorie 2", "catégorie 3"]
    form = bdese_form_factory(bdese_50_300, step, categories_professionnelles)

    assert form.instance == bdese_50_300
    assert len(form.fields) == len(BDESE_50_300_FIELDS[step]) + 1
    assert "indicateurs_externes_in_step" in form.fields
    for field in BDESE_50_300_FIELDS[step]:
        assert field in form.fields

    for field in [
        field for field in form.fields if field in bdese_50_300.category_fields()
    ]:
        assert isinstance(form.fields[field], forms.MultiValueField)

    for field in form.fields:
        if field == "indicateurs_externes_in_step":
            assert form[field].value() == json.dumps([])
        else:
            assert not form[field].value()

    bound_form = bdese_form_factory(
        bdese_50_300, step, categories_professionnelles, data={}
    )

    assert bound_form.is_valid(), bound_form.errors


def categories_form_data(categories_pro, categories_pro_detaillees=None):
    data = {
        f"categories_professionnelles_{i}": categories_pro[i]
        for i in range(len(categories_pro))
    }
    if categories_pro_detaillees:
        for i in range(len(categories_pro_detaillees)):
            data[
                f"categories_professionnelles_detaillees_{i}"
            ] = categories_pro_detaillees[i]
    return data


def test_categories_professionnelles_form_for_bdese_50_300(bdese_50_300):
    form = categories_professionnelles_form_factory(bdese_50_300)

    assert len(form.fields) == 1
    assert "categories_professionnelles" in form.fields

    categories_pro = ["catégorie 1", "catégorie 2", "catégorie 3"]
    bound_form = categories_professionnelles_form_factory(
        bdese_50_300,
        data=categories_form_data(categories_pro),
    )
    bdese_50_300 = bound_form.save()

    assert bdese_50_300.categories_professionnelles == categories_pro


def test_categories_professionnelles_form_for_bdese_300(bdese_300):
    form = categories_professionnelles_form_factory(bdese_300)

    assert len(form.fields) == 2
    assert "categories_professionnelles" in form.fields
    assert "categories_professionnelles_detaillees" in form.fields

    categories_pro = ["catégorie 1", "catégorie 2", "catégorie 3"]
    categories_pro_detaillees = [
        "catégorie détaillée 1",
        "catégorie détaillée 2",
        "catégorie détaillée 3",
        "catégorie détaillée 4",
        "catégorie détaillée 5",
    ]

    bound_form = categories_professionnelles_form_factory(
        bdese_300,
        data=categories_form_data(categories_pro, categories_pro_detaillees),
    )
    bdese_300 = bound_form.save()

    assert bdese_300.categories_professionnelles == categories_pro
    assert bdese_300.categories_professionnelles_detaillees == categories_pro_detaillees


def test_at_least_3_categories_professionnelles(bdese):
    categories_pro = ["catégorie 1", "catégorie 2"]
    bound_form = categories_professionnelles_form_factory(
        bdese,
        data=categories_form_data(categories_pro),
    )

    assert not bound_form.is_valid()


def test_at_least_5_categories_professionnelles_detaillees(bdese_300):
    categories_pro = ["catégorie 1", "catégorie 2", "catégorie 3"]
    categories_pro_detaillees = [
        "catégorie détaillée 1",
        "catégorie détaillée 2",
        "catégorie détaillée 3",
        "catégorie détaillée 4",
    ]
    bound_form = categories_professionnelles_form_factory(
        bdese_300,
        data=categories_form_data(categories_pro, categories_pro_detaillees),
    )

    assert not bound_form.is_valid()


def test_categories_professionnelles_of_complete_step_are_disabled(bdese):
    bdese.mark_step_as_complete(0)

    form = categories_professionnelles_form_factory(bdese)

    for field in form.fields:
        assert form.fields[field].disabled
