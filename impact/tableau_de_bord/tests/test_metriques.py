import pytest

from reglementations.views import REGLEMENTATIONS
from tableau_de_bord.metriques import calculer_metriques_entreprise
from vsme.models import RapportVSME


def test_metriques_entreprise_non_qualifiee(entreprise_non_qualifiee):
    metriques = calculer_metriques_entreprise(entreprise_non_qualifiee)

    assert metriques == {
        "nombre_reglementations_applicables": "?",
        "pourcentage_vsme": 0,
    }


def test_metriques_entreprise_etrangere_sans_reglementations_applicables(
    entreprise_factory,
):
    entreprise = entreprise_factory(code_pays="MAR", identifiant="001234567000089")

    metriques = calculer_metriques_entreprise(entreprise)

    assert metriques["nombre_reglementations_applicables"] is None


@pytest.mark.parametrize("est_soumis", [True, False])
def test_metriques_nombre_de_reglementations_applicables(
    est_soumis, entreprise_factory, mocker
):
    entreprise = entreprise_factory()
    for REGLEMENTATION in REGLEMENTATIONS:
        mocker.patch(
            f"{REGLEMENTATION.__module__}.{REGLEMENTATION.__name__}.est_soumis",
            return_value=est_soumis,
        )

    metriques = calculer_metriques_entreprise(entreprise)

    if est_soumis:
        assert metriques["nombre_reglementations_applicables"] == len(REGLEMENTATIONS)
    else:
        assert metriques["nombre_reglementations_applicables"] == 0


def test_metriques_pourcentage_vsme_nul_sans_rapport(entreprise_factory):
    entreprise = entreprise_factory()

    metriques = calculer_metriques_entreprise(entreprise)

    assert metriques["pourcentage_vsme"] == 0


def test_metriques_pourcentage_vsme_du_rapport_du_dernier_exercice_clos(
    entreprise_factory, mocker
):
    entreprise = entreprise_factory()
    RapportVSME.objects.create(
        entreprise=entreprise,
        annee=entreprise.dernier_exercice_clos.date_cloture.year,
    )
    mocker.patch.object(RapportVSME, "progression", return_value={"pourcent": 42})

    metriques = calculer_metriques_entreprise(entreprise)

    assert metriques["pourcentage_vsme"] == 42


def test_metriques_ignore_le_rapport_vsme_d_une_autre_annee(
    entreprise_factory, mocker
):
    entreprise = entreprise_factory()
    RapportVSME.objects.create(
        entreprise=entreprise,
        annee=entreprise.dernier_exercice_clos.date_cloture.year - 1,
    )
    mocker.patch.object(RapportVSME, "progression", return_value={"pourcent": 42})

    metriques = calculer_metriques_entreprise(entreprise)

    assert metriques["pourcentage_vsme"] == 0
