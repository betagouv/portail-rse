from django.db.utils import IntegrityError
import pytest

from reglementations.models import BDESE_300, BDESE_50_300


@pytest.mark.django_db(transaction=True)
def test_bdese_300(grande_entreprise):
    with pytest.raises(IntegrityError):
        BDESE_300.objects.create()

    bdese = BDESE_300.objects.create(entreprise=grande_entreprise)

    assert bdese.annee == 2022
    assert bdese.entreprise == grande_entreprise
    assert "effectif_total" in bdese.category_fields()
    assert bdese.effectif_total is None
    assert "nombre_travailleurs_exterieurs" not in bdese.category_fields()
    assert bdese.nombre_travailleurs_exterieurs is None
    assert not bdese.is_complete
    for step in range(1, len(bdese.STEPS)):
        assert not bdese.step_is_complete(step)

    with pytest.raises(KeyError):
        assert not bdese.step_is_complete(len(bdese.STEPS) + 1)

    for step in bdese.STEPS:
        bdese.mark_step_as_complete(step)
        assert bdese.step_is_complete(step)

        bdese.mark_step_as_incomplete(step)
        assert not bdese.step_is_complete(step)


@pytest.mark.django_db(transaction=True)
def test_bdese_50_300(grande_entreprise):
    with pytest.raises(IntegrityError):
        BDESE_50_300.objects.create()

    bdese = BDESE_50_300.objects.create(entreprise=grande_entreprise)

    assert bdese.annee == 2022
    assert bdese.entreprise == grande_entreprise
    assert "effectif_mensuel" in bdese.category_fields()
    assert bdese.effectif_mensuel is None
    assert "effectif_cdi" not in bdese.category_fields()
    assert bdese.effectif_cdi is None
    assert not bdese.is_complete
