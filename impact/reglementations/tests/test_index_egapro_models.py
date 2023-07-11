from freezegun import freeze_time

from reglementations.models import derniere_annee_a_remplir_index_egapro


def test_derniere_annee_a_remplir_index_egapro():
    with freeze_time("2022-11-23"):
        annee = derniere_annee_a_remplir_index_egapro()
        assert annee == 2021

    with freeze_time("2023-11-23"):
        annee = derniere_annee_a_remplir_index_egapro()
        assert annee == 2022
