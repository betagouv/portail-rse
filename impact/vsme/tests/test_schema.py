import pytest

from vsme.schema import EXIGENCES_DE_PUBLICATION


@pytest.mark.parametrize(
    "exigence",
    [
        exigence
        for exigence in EXIGENCES_DE_PUBLICATION.values()
        if exigence.remplissable
    ],
)
def test_exigence_remplissable_a_des_indicateurs_valides(exigence):
    indicateurs = exigence.indicateurs_schemas()

    assert len(indicateurs) > 0, f"L'exigence {exigence.code} n'a aucun indicateur"
    for indicateur in indicateurs:
        assert indicateur.schema_id
        assert indicateur.titre
        assert indicateur.description
        assert indicateur.ancre
        assert len(indicateur.champs) > 0
