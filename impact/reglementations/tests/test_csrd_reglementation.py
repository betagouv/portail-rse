import pytest
from django.urls import reverse

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.csrd import CSRDReglementation


def test_reglementation_info():
    info = CSRDReglementation.info()

    assert info["title"] == "Rapport de durabilité - Directive CSRD"
    assert info["more_info_url"] == reverse("reglementations:fiche_csrd")
    assert info["tag"] == "tag-durabilite"
    assert info["summary"] == "Publier un rapport de durabilité"


@pytest.fixture
def _caracteristiques_suffisamment_qualifiantes_sans_groupe(entreprise_factory):
    entreprise = entreprise_factory(
        est_cotee=False,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
    )
    return entreprise.dernieres_caracteristiques


def test_est_suffisamment_qualifiee_sans_groupe(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe

    assert CSRDReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_est_cotee_non_renseigne(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.entreprise.est_cotee = None

    assert not CSRDReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_sans_effectif(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.effectif = None

    assert not CSRDReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_sans_CA(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.tranche_chiffre_affaires = None

    assert not CSRDReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_sans_bilan(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.tranche_bilan = None

    assert not CSRDReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_groupe_non_renseigne(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.entreprise.appartient_groupe = None

    assert not CSRDReglementation.est_suffisamment_qualifiee(caracteristiques)


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_20M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
def test_entreprise_non_cotee_bilan_et_ca_superieurs_aux_seuils_soumise_en_2026(
    bilan, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=False,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2026
    )
