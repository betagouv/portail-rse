from datetime import date

from freezegun import freeze_time

from reglementations.models import derniere_annee_a_remplir_index_egapro
from reglementations.models import prochaine_echeance_index_egapro


def test_derniere_annee_a_remplir_index_egapro():
    with freeze_time("2022-11-23"):
        annee = derniere_annee_a_remplir_index_egapro()
        assert annee == 2021

    with freeze_time("2023-11-23"):
        annee = derniere_annee_a_remplir_index_egapro()
        assert annee == 2022


def test_prochaine_echance_index_gapro():
    with freeze_time("2023-02-28"):
        prochaine_echeance = prochaine_echeance_index_egapro(
            derniere_annee_est_publiee=False
        )
        assert prochaine_echeance == date(2023, 3, 1)

    with freeze_time("2023-02-28"):
        prochaine_echeance = prochaine_echeance_index_egapro(
            derniere_annee_est_publiee=True
        )
        assert prochaine_echeance == date(2024, 3, 1)

    with freeze_time("2023-03-02"):
        prochaine_echeance = prochaine_echeance_index_egapro(
            derniere_annee_est_publiee=False
        )
        assert prochaine_echeance == date(2023, 3, 1)

    with freeze_time("2023-03-01"):
        prochaine_echeance = prochaine_echeance_index_egapro(
            derniere_annee_est_publiee=True
        )
        assert prochaine_echeance == date(2024, 3, 1)
