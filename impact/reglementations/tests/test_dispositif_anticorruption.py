import pytest
from django.urls import reverse

from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from reglementations.views.base import ReglementationStatus
from reglementations.views.dispositif_anticorruption import DispositifAntiCorruption


def test_reglementation_info():
    info = DispositifAntiCorruption.info()

    assert info["title"] == "Dispositif anti-corruption"
    assert info["more_info_url"] == reverse(
        "reglementations:fiche_dispositif_anticorruption"
    )
    assert info["tag"] == "tag-gouvernance"
    assert (
        info["summary"]
        == "Se doter d'un dispositif efficace pour lutter contre la corruption et le trafic d'influence."
    )


@pytest.fixture
def _caracteristiques_suffisamment_qualifiantes_sans_groupe(entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
        appartient_groupe=False,
        comptes_consolides=None,
    )
    return entreprise.dernieres_caracteristiques


@pytest.fixture
def _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        siren="000000002",
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
        appartient_groupe=True,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        comptes_consolides=False,
    )
    return entreprise.dernieres_caracteristiques


@pytest.fixture
def _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        siren="000000003",
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
        appartient_groupe=True,
        comptes_consolides=True,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    return entreprise.dernieres_caracteristiques


def test_est_suffisamment_qualifiee(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides,
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe

    assert DispositifAntiCorruption.est_suffisamment_qualifiee(caracteristiques)

    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides
    )

    assert DispositifAntiCorruption.est_suffisamment_qualifiee(caracteristiques)

    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides
    )

    assert DispositifAntiCorruption.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_sans_effectif(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.effectif = None

    assert not DispositifAntiCorruption.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_sans_CA(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.tranche_chiffre_affaires = None

    assert not DispositifAntiCorruption.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_groupe_non_renseigne(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.entreprise.appartient_groupe = None

    assert not DispositifAntiCorruption.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_groupe_mais_sans_effectif_groupe(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides,
):
    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides
    )
    caracteristiques.effectif_groupe = None

    assert not DispositifAntiCorruption.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_groupe_mais_comptes_consolides_non_renseigne(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides,
):
    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides
    )
    caracteristiques.entreprise.comptes_consolides = None

    assert not DispositifAntiCorruption.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_comptes_consolides_mais_sans_CA_consolide(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides,
):
    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides
    )
    caracteristiques.tranche_chiffre_affaires_consolide = None

    assert not DispositifAntiCorruption.est_suffisamment_qualifiee(caracteristiques)


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
    ],
)
def test_calcule_etat_avec_effectif_insuffisant(effectif, entreprise_factory, alice):
    entreprise = entreprise_factory(
        effectif=effectif,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DispositifAntiCorruption.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )


@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
        CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
    ],
)
def test_calcule_etat_avec_ca_insuffisant(ca, entreprise_factory, alice):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        tranche_chiffre_affaires=ca,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DispositifAntiCorruption.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calcule_etat_seuils_effectif_et_ca_suffisants(
    effectif, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        effectif=effectif,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DispositifAntiCorruption.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 500 salariés et votre chiffre d'affaires est supérieur à 100 millions d'euros."
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calcule_etat_seuils_effectif_et_ca_consolide_suffisants(
    effectif, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        comptes_consolides=True,
        effectif=effectif,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DispositifAntiCorruption.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 500 salariés et votre chiffre d'affaires consolidé est supérieur à 100 millions d'euros."
    )


def test_calcule_etat_seuils_effectif_ca_et_ca_consolide_suffisants(
    entreprise_factory, alice
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DispositifAntiCorruption.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 500 salariés et votre chiffre d'affaires est supérieur à 100 millions d'euros."
    )


@pytest.mark.parametrize(
    "effectif_groupe",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calcule_etat_seuils_effectif_groupe_et_ca_suffisants(
    effectif_groupe, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        societe_mere_en_france=True,
        effectif_groupe=effectif_groupe,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DispositifAntiCorruption.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car l'effectif du groupe est supérieur à 500 salariés et votre chiffre d'affaires est supérieur à 100 millions d'euros."
    )


@pytest.mark.parametrize(
    "effectif_groupe",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calcule_etat_seuils_effectif_groupe_et_ca_suffisants_mais_siege_social_a_l_etranger(
    effectif_groupe, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        societe_mere_en_france=False,
        effectif_groupe=effectif_groupe,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DispositifAntiCorruption.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )
