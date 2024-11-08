from datetime import date

import pytest
from django.urls import reverse

from conftest import CODE_AUTRE
from conftest import CODE_PAYS_CANADA
from conftest import CODE_SA
from conftest import CODE_SA_COOPERATIVE
from conftest import CODE_SAS
from conftest import CODE_SCA
from conftest import CODE_SE
from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from reglementations.enums import ESRS
from reglementations.models import RapportCSRD
from reglementations.views.base import ReglementationStatus
from reglementations.views.csrd import CSRDReglementation


def test_reglementation_info():
    info = CSRDReglementation.info()

    assert info["title"] == "Rapport de Durabilité - CSRD"
    assert info["more_info_url"] == reverse("reglementations:fiche_csrd")
    assert info["tag"] == "tag-durabilite"
    assert info["summary"] == "Publier un rapport de durabilité."
    assert info["zone"] == "europe"


@pytest.fixture
def _caracteristiques_suffisamment_qualifiantes_sans_groupe(entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        date_cloture_exercice=date(2023, 12, 31),
        est_cotee=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        appartient_groupe=False,
    )
    return entreprise.dernieres_caracteristiques


@pytest.fixture
def _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        siren="000000002",
        date_cloture_exercice=date(2023, 12, 31),
        est_cotee=False,
        est_interet_public=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        appartient_groupe=True,
        comptes_consolides=False,
    )
    return entreprise.dernieres_caracteristiques


@pytest.fixture
def _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        siren="000000003",
        date_cloture_exercice=date(2023, 12, 31),
        est_cotee=False,
        est_interet_public=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    return entreprise.dernieres_caracteristiques


def test_est_suffisamment_qualifiee(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides,
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe

    assert CSRDReglementation.est_suffisamment_qualifiee(caracteristiques)

    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides
    )

    assert CSRDReglementation.est_suffisamment_qualifiee(caracteristiques)

    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides
    )

    assert CSRDReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_date_cloture_exercice_non_renseignee(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.date_cloture_exercice = None

    assert not CSRDReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_est_cotee_non_renseigne(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.entreprise.est_cotee = None

    assert not CSRDReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_est_interet_public_non_renseigne(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.entreprise.est_interet_public = None

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


def test_n_est_pas_suffisamment_qualifiee_car_groupe_mais_comptes_consolides_non_renseigne(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides,
):
    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides
    )
    caracteristiques.entreprise.comptes_consolides = None

    assert not CSRDReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_comptes_consolides_mais_sans_effectif_groupe(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides,
):
    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides
    )
    caracteristiques.effectif_groupe = None

    assert not CSRDReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_comptes_consolides_mais_sans_bilan_consolide(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides,
):
    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides
    )
    caracteristiques.tranche_bilan_consolide = None

    assert not CSRDReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_comptes_consolides_mais_sans_ca_consolide(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides,
):
    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides
    )
    caracteristiques.tranche_chiffre_affaires_consolide = None

    assert not CSRDReglementation.est_suffisamment_qualifiee(caracteristiques)


@pytest.mark.parametrize(
    "categorie_juridique_sirene",
    [
        3205,  # Organisation internationale
        3220,  # Société étrangère non immatriculée au RCS
        6210,  # GEIE
        6220,  # GIE
        6511,  # Sociétés Interprofessionnelles de Soins Ambulatoires
        6540,  # SCI
        7490,  # Autre personne morale de droit administratif
        CODE_AUTRE,  # congrégation
    ],
)
def test_entreprise_hors_categorie_juridique_concernee_sans_interet_public_non_soumise(
    categorie_juridique_sirene, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=categorie_juridique_sirene,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        est_interet_public=False,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert not CSRDReglementation.est_soumis_a_partir_de_l_exercice(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "categorie_juridique_sirene",
    [
        3205,  # Organisation internationale
        3220,  # Société étrangère non immatriculée au RCS
        6210,  # GEIE
        6220,  # GIE
        6511,  # Sociétés Interprofessionnelles de Soins Ambulatoires
        6540,  # SCI
        7490,  # Autre personne morale de droit administratif
        CODE_AUTRE,  # congrégation
    ],
)
def test_entreprise_hors_categorie_juridique_concernee_avec_interet_public_soumise(
    categorie_juridique_sirene, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=categorie_juridique_sirene,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        est_interet_public=True,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "categorie_juridique_sirene",
    [
        3120,  # Société commerciale étrangère immatriculée au RCS
        5191,  # Société de caution mutuelle
        CODE_SCA,
        CODE_SA,
        CODE_SA_COOPERATIVE,
        CODE_SAS,
        CODE_SE,
        6100,  # Caisse d'Épargne et de Prévoyance
        6316,  # Coopérative d'utilisation de matériel agricole en commun (CUMA)
        6411,  # Société d'assurance à forme mutuelle
        8110,  # Régime général de la Sécurité Sociale
        8290,  # Autre organisme mutualiste
    ],
)
def test_entreprise_categorie_juridique_concernee_soumise(
    categorie_juridique_sirene, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=categorie_juridique_sirene,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        est_interet_public=False,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_25M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
def test_entreprise_non_cotee_bilan_et_ca_superieurs_aux_seuils_grande_entreprises_soumise_en_2025(
    bilan, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2025
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre bilan est supérieur à 25M€",
        "votre chiffre d'affaires est supérieur à 50M€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_25M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_entreprise_non_cotee_bilan_et_effectif_superieurs_aux_seuils_grande_entreprise_soumise_en_2025(
    bilan, effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2025
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre effectif est supérieur à 250 salariés",
        "votre bilan est supérieur à 25M€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_entreprise_non_cotee_CA_et_effectif_superieurs_aux_seuils_grande_entreprise_soumise_en_2025(
    ca, effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=ca,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2025
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre effectif est supérieur à 250 salariés",
        "votre chiffre d'affaires est supérieur à 50M€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_25M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_entreprise_sans_interet_public_bilan_et_effectif_superieurs_aux_seuils_grande_entreprise_soumise_en_2025(
    bilan, effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        est_interet_public=False,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2025
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre effectif est supérieur à 250 salariés",
        "votre bilan est supérieur à 25M€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_entreprise_sans_interet_public_CA_et_effectif_superieurs_aux_seuils_grande_entreprise_soumise_en_2025(
    ca, effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        est_interet_public=False,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=ca,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2025
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre effectif est supérieur à 250 salariés",
        "votre chiffre d'affaires est supérieur à 50M€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
    ],
)
def test_entreprise_non_cotee_bilan_et_CA_inferieurs_aux_seuils_grande_entreprise_non_soumise(
    ca, bilan, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert not CSRDReglementation.est_soumis_a_partir_de_l_exercice(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
    ],
)
def test_entreprise_non_cotee_avec_interet_public_bilan_et_CA_inferieurs_aux_seuils_grande_entreprise_non_soumise(
    ca, bilan, entreprise_factory
):
    """l'intérêt public d'une PME n'est pas une condition mais empêche une implémentation naive"""
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        est_interet_public=True,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert not CSRDReglementation.est_soumis_a_partir_de_l_exercice(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
    ],
)
def test_entreprise_non_cotee_effectif_et_CA_inferieurs_aux_seuils_grande_entreprise_non_soumise(
    effectif, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=ca,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert not CSRDReglementation.est_soumis_a_partir_de_l_exercice(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
    ],
)
@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
    ],
)
def test_entreprise_non_cotee_effectif_et_bilan_inferieurs_aux_seuils_grande_entreprise_non_soumise(
    effectif, bilan, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert not CSRDReglementation.est_soumis_a_partir_de_l_exercice(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_microentreprise_cotee_car_seuils_bilan_et_ca_insuffisants_est_non_soumise(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert not CSRDReglementation.est_soumis_a_partir_de_l_exercice(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_microentreprise_cotee_car_seuils_effectif_et_bilan_insuffisants_est_non_soumise(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert not CSRDReglementation.est_soumis_a_partir_de_l_exercice(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_microentreprise_cotee_car_seuil_effectif_et_ca_insuffisants_est_non_soumise(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert not CSRDReglementation.est_soumis_a_partir_de_l_exercice(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_microentreprise_cotee_car_aucun_seuil_suffisant_est_non_soumise(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert not CSRDReglementation.est_soumis_a_partir_de_l_exercice(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_entreprise_cotee_ca_et_effectif_plus_de_500_superieurs_aux_seuils_grande_entreprise_soumise_en_2024(
    ca, effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        est_interet_public=False,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=ca,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2024
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre effectif est supérieur à 500 salariés",
        "votre chiffre d'affaires est supérieur à 50M€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_entreprise_interet_public_ca_et_effectif_plus_de_500_superieurs_aux_seuils_grande_entreprise_soumise_en_2024(
    ca, effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        est_interet_public=True,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=ca,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2024
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est d'intérêt public",
        "votre effectif est supérieur à 500 salariés",
        "votre chiffre d'affaires est supérieur à 50M€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
    ],
)
def test_entreprise_cotee_ca_et_effectif_moins_de_500_superieurs_aux_seuils_grande_entreprise_soumise_en_2025(
    ca, effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=ca,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2025
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre effectif est supérieur à 250 salariés",
        "votre chiffre d'affaires est supérieur à 50M€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_25M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
def test_entreprise_cotee_bilan_et_ca_superieurs_aux_seuils_petite_entreprise_mais_ca_inferieur_seuil_grande_entreprise_soumise_en_2026(
    bilan, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2026
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre bilan est supérieur à 450k€",
        "votre chiffre d'affaires est supérieur à 900k€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
def test_entreprise_cotee_bilan_et_ca_superieurs_aux_seuils_petite_entreprise_mais_bilan_inferieur_seuil_grande_entreprise_soumise_en_2026(
    ca, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        tranche_chiffre_affaires=ca,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2026
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre bilan est supérieur à 450k€",
        "votre chiffre d'affaires est supérieur à 900k€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_entreprise_cotee_effectif_et_ca_superieurs_aux_seuils_petite_entreprise_mais_ca_inferieur_seuil_grande_entreprise_soumise_en_2026(
    effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2026
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre effectif est supérieur à 10 salariés",
        "votre chiffre d'affaires est supérieur à 900k€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
def test_entreprise_cotee_effectif_et_ca_superieurs_aux_seuils_petite_entreprise_mais_effectif_inferieur_seuil_grande_entreprise_soumise_en_2026(
    effectif, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=ca,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2026
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre effectif est supérieur à 10 salariés",
        "votre chiffre d'affaires est supérieur à 900k€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_entreprise_cotee_effectif_et_bilan_superieurs_aux_seuils_petite_entreprise_mais_bilan_inferieur_seuil_grande_entreprise_soumise_en_2026(
    effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2026
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre effectif est supérieur à 10 salariés",
        "votre bilan est supérieur à 450k€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
    ],
)
@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_25M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
def test_entreprise_cotee_effectif_et_bilan_superieurs_aux_seuils_petite_entreprise_mais_effectif_inferieur_seuil_grande_entreprise_soumise_en_2026(
    effectif, bilan, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2026
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre effectif est supérieur à 10 salariés",
        "votre bilan est supérieur à 450k€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_calcule_etat_si_non_soumis(entreprise_factory, alice):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = CSRDReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )
    assert (
        reglementation.primary_action.title
        == "Accéder à l'espace Rapport de Durabilité"
    )
    assert reglementation.primary_action.url == reverse(
        "reglementations:gestion_csrd",
        kwargs={
            "siren": entreprise.siren,
            "id_etape": "introduction",
        },
    )


def test_calcule_etat_si_soumis_en_2025_et_delegable(entreprise_factory, alice):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=True,
        est_societe_mere=False,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = CSRDReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation à partir de 2025 sur les données de l'exercice comptable 2024 car votre société est cotée sur un marché réglementé, l'effectif du groupe est supérieur à 500 salariés, le bilan du groupe est supérieur à 30M€ et le chiffre d'affaires du groupe est supérieur à 60M€. Vous pouvez déléguer cette obligation à votre société-mère. Vous devez publier le Rapport de Durabilité en même temps que le rapport de gestion."
    )
    assert reglementation.prochaine_echeance == 2025
    assert (
        reglementation.primary_action.title
        == "Accéder à l'espace Rapport de Durabilité"
    )
    assert reglementation.primary_action.url == reverse(
        "reglementations:gestion_csrd",
        kwargs={
            "siren": entreprise.siren,
            "id_etape": "introduction",
        },
    )


def test_calcule_etat_si_soumis_en_2027_et_non_delegable(entreprise_factory, alice):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = CSRDReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation à partir de 2027 sur les données de l'exercice comptable 2026 car votre société est cotée sur un marché réglementé, votre effectif est supérieur à 10 salariés et votre bilan est supérieur à 450k€. Vous devez publier le Rapport de Durabilité en même temps que le rapport de gestion."
    )
    assert reglementation.prochaine_echeance == 2027
    assert (
        reglementation.primary_action.title
        == "Accéder à l'espace Rapport de Durabilité"
    )
    assert reglementation.primary_action.url == reverse(
        "reglementations:gestion_csrd",
        kwargs={
            "siren": entreprise.siren,
            "id_etape": "introduction",
        },
    )


def test_calcule_etat_si_entreprise_hors_EEE_soumise_en_2029_sous_condition(
    entreprise_factory, alice
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=CODE_PAYS_CANADA,
        est_cotee=False,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = CSRDReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation à partir de 2029 sur les données de l'exercice comptable 2028 si votre société dont le siège social est hors EEE revêt une forme juridique comparable aux sociétés par actions ou aux sociétés à responsabilité limitée, comptabilise un chiffre d'affaires net dans l'Espace économique européen qui excède 150 millions d'euros à la date de clôture des deux derniers exercices consécutifs, ne contrôle ni n'est contrôlée par une autre société et dispose d'une succursale en France dont le chiffre d'affaires net excède 40 millions d'euros. Vous devez publier le Rapport de Durabilité en même temps que le rapport de gestion."
    )
    assert reglementation.prochaine_echeance == 2029


@pytest.mark.parametrize("est_cotee", [False, True])
def test_microentreprise_filiale_grand_groupe_jamais_soumise(
    est_cotee, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=est_cotee,
        appartient_groupe=True,
        est_societe_mere=False,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_microentreprise_cotee_societe_mere_grand_groupe_effectif_groupe_superieur_a_500_soumise_en_2024(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        est_interet_public=False,
        appartient_groupe=True,
        est_societe_mere=True,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2024
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre société est la société mère d'un groupe",
        "l'effectif du groupe est supérieur à 500 salariés",
        "le bilan du groupe est supérieur à 30M€",
        "le chiffre d'affaires du groupe est supérieur à 60M€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_microentreprise_cotee_societe_mere_grand_groupe_effectif_groupe_inferieur_a_500_soumise_en_2025(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        est_interet_public=False,
        appartient_groupe=True,
        est_societe_mere=True,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2025
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre société est la société mère d'un groupe",
        "l'effectif du groupe est supérieur à 250 salariés",
        "le bilan du groupe est supérieur à 30M€",
        "le chiffre d'affaires du groupe est supérieur à 60M€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_microentreprise_avec_interet_public_societe_mere_grand_groupe_effectif_groupe_superieur_a_500_soumise_en_2024(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        est_interet_public=True,
        appartient_groupe=True,
        est_societe_mere=True,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2024
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est d'intérêt public",
        "votre société est la société mère d'un groupe",
        "l'effectif du groupe est supérieur à 500 salariés",
        "le bilan du groupe est supérieur à 30M€",
        "le chiffre d'affaires du groupe est supérieur à 60M€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_microentreprise_avec_interet_public_societe_mere_grand_groupe_effectif_groupe_inferieur_a_500_soumise_en_2025(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        est_interet_public=True,
        appartient_groupe=True,
        est_societe_mere=True,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2025
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est d'intérêt public",
        "votre société est la société mère d'un groupe",
        "l'effectif du groupe est supérieur à 250 salariés",
        "le bilan du groupe est supérieur à 30M€",
        "le chiffre d'affaires du groupe est supérieur à 60M€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_microentreprise_non_cotee_sans_interet_public_societe_mere_grand_groupe_soumise_en_2025(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        appartient_groupe=True,
        est_societe_mere=True,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2025
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est la société mère d'un groupe",
        "l'effectif du groupe est supérieur à 250 salariés",
        "le bilan du groupe est supérieur à 30M€",
        "le chiffre d'affaires du groupe est supérieur à 60M€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_PME_cotee_filiale_grand_groupe_effectif_groupe_superieur_a_500_soumise_en_2024(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=True,
        est_societe_mere=False,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2024
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "l'effectif du groupe est supérieur à 500 salariés",
        "le bilan du groupe est supérieur à 30M€",
        "le chiffre d'affaires du groupe est supérieur à 60M€",
    ]
    assert CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_PME_cotee_filiale_grand_groupe_effectif_groupe_inferieur_a_500_soumise_en_2025(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=True,
        est_societe_mere=False,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2025
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "l'effectif du groupe est supérieur à 250 salariés",
        "le bilan du groupe est supérieur à 30M€",
        "le chiffre d'affaires du groupe est supérieur à 60M€",
    ]
    assert CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_PME_non_cotee_filiale_grand_groupe_non_soumise(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        appartient_groupe=True,
        est_societe_mere=False,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_grande_entreprise_cotee_filiale_ne_peut_pas_deleguer(
    effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=True,
        est_societe_mere=False,
        comptes_consolides=True,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_grande_entreprise_non_cotee_filiale_peut_deleguer(entreprise_factory):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        appartient_groupe=True,
        est_societe_mere=False,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
    ],
)
def test_micro_ou_PME_hors_EEE_effectif_et_ca_inferieurs_seuils_grande_entreprise_et_CA_inferieur_à_100M(
    effectif,
    ca,
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=CODE_PAYS_CANADA,
        est_cotee=False,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=ca,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
    ],
)
def test_micro_ou_PME_hors_EEE_bilan_et_ca_inferieurs_seuils_grande_entreprise_et_CA_inferieur_à_100M(
    bilan,
    ca,
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=CODE_PAYS_CANADA,
        est_cotee=False,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
    ],
)
@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
    ],
)
def test_micro_ou_PME_hors_EEE_effectif_et_bilan_inferieurs_seuils_grande_entreprise_et_CA_inferieur_à_100M(
    effectif,
    bilan,
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=CODE_PAYS_CANADA,
        est_cotee=False,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
    ],
)
@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
    ],
)
def test_micro_ou_PME_hors_EEE_CA_supérieur_à_100M(
    effectif,
    bilan,
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=CODE_PAYS_CANADA,
        est_cotee=False,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2028
    )
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_25M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
def test_entreprise_hors_EEE_bilan_et_ca_superieurs_aux_seuils_grande_entreprise(
    bilan,
    ca,
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=CODE_PAYS_CANADA,
        est_cotee=False,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2025
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre siège social est hors EEE",
        "votre bilan est supérieur à 25M€",
        "votre chiffre d'affaires est supérieur à 50M€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_25M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_entreprise_hors_EEE_bilan_et_effectif_superieurs_aux_seuils_grande_entreprise(
    bilan, effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=CODE_PAYS_CANADA,
        est_cotee=False,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2025
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre siège social est hors EEE",
        "votre effectif est supérieur à 250 salariés",
        "votre bilan est supérieur à 25M€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_entreprise_hors_EEE_ca_et_effectif_superieurs_aux_seuils_grande_entreprise(
    ca, effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=CODE_PAYS_CANADA,
        est_cotee=False,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=ca,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de_l_exercice(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2025
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre siège social est hors EEE",
        "votre effectif est supérieur à 250 salariés",
        "votre chiffre d'affaires est supérieur à 50M€",
    ]
    assert not CSRDReglementation.est_delegable(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_decale_annee_publication_selon_cloture_exercice_comptable():
    caracteristiques = CaracteristiquesAnnuelles(
        date_cloture_exercice=date(2023, 12, 31)
    )
    assert (
        CSRDReglementation.decale_annee_publication_selon_cloture_exercice_comptable(
            2024, caracteristiques
        )
        == 2025
    )

    caracteristiques = CaracteristiquesAnnuelles(
        date_cloture_exercice=date(2023, 11, 30)
    )
    assert (
        CSRDReglementation.decale_annee_publication_selon_cloture_exercice_comptable(
            2024, caracteristiques
        )
        == 2026
    )

    caracteristiques = CaracteristiquesAnnuelles(
        date_cloture_exercice=date(2023, 7, 31)
    )
    assert (
        CSRDReglementation.decale_annee_publication_selon_cloture_exercice_comptable(
            2024, caracteristiques
        )
        == 2026
    )

    caracteristiques = CaracteristiquesAnnuelles(
        date_cloture_exercice=date(2023, 6, 30)
    )
    assert (
        CSRDReglementation.decale_annee_publication_selon_cloture_exercice_comptable(
            2024, caracteristiques
        )
        == 2025
    )

    caracteristiques = CaracteristiquesAnnuelles(
        date_cloture_exercice=date(2023, 1, 31)
    )
    assert (
        CSRDReglementation.decale_annee_publication_selon_cloture_exercice_comptable(
            2024, caracteristiques
        )
        == 2025
    )


def test_decale_annee_publication_selon_cloture_exercice_comptable_le_28_fevrier_bissextile():
    # Ce cas est arrivé en prod
    caracteristiques = CaracteristiquesAnnuelles(
        date_cloture_exercice=date(2024, 2, 28)
    )
    assert (
        CSRDReglementation.decale_annee_publication_selon_cloture_exercice_comptable(
            2025, caracteristiques
        )
        == 2026
    )

    caracteristiques = CaracteristiquesAnnuelles(
        date_cloture_exercice=date(2024, 2, 29)
    )
    assert (
        CSRDReglementation.decale_annee_publication_selon_cloture_exercice_comptable(
            2025, caracteristiques
        )
        == 2026
    )


def test_calcule_etat_si_soumis_en_2026_car_exercice_comptable_different_annee_civile(
    entreprise_factory, alice
):
    entreprise = entreprise_factory(
        date_cloture_exercice=date(2023, 11, 30),
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=True,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = CSRDReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail.startswith(
        "Vous êtes soumis à cette réglementation à partir de 2026 sur les données de l'exercice comptable 2024-2025 car"
    )
    assert reglementation.status_detail.endswith(
        "Vous devez publier le Rapport de Durabilité en même temps que le rapport de gestion."
    )
    assert reglementation.prochaine_echeance == 2026


def test_calcule_etat_avec_CSRD_initialisée(entreprise_factory, alice):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
    )
    habilitation = attach_user_to_entreprise(alice, entreprise, "Présidente")
    RapportCSRD.objects.create(
        entreprise=entreprise,
        proprietaire=alice,
        annee=date.today().year,
    )

    reglementation = CSRDReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert (
        reglementation.primary_action.title
        == "Accéder à l'espace Rapport de Durabilité"
    )
    assert reglementation.primary_action.url == reverse(
        "reglementations:gestion_csrd",
        kwargs={
            "siren": entreprise.siren,
            "id_etape": "introduction",
        },
    )


def test_calcule_etat_avec_CSRD_et_étapes_validées(entreprise_factory, alice):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        est_cotee=False,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
    )
    habilitation = attach_user_to_entreprise(alice, entreprise, "Présidente")
    DEJA_VALIDEE = "selection-enjeux"
    RapportCSRD.objects.create(
        entreprise=entreprise,
        proprietaire=alice,
        annee=date.today().year,
        etape_validee=DEJA_VALIDEE,
    )

    reglementation = CSRDReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.primary_action.title == "Reprendre ma CSRD"
    assert reglementation.primary_action.url == reverse(
        "reglementations:gestion_csrd",
        kwargs={
            "siren": entreprise.siren,
            "id_etape": "analyse-materialite",
        },
    )


def test_themes_ESRS():
    assert ESRS.theme("ESRS_E2") == "environnement"
    assert ESRS.theme("ESRS_S3") == "social"
    assert ESRS.theme("ESRS_G1") == "gouvernance"


def test_titres_ESRS():
    assert ESRS.titre("ESRS_E2") == "ESRS E2 - Pollution"
    assert ESRS.titre("ESRS_S3") == "ESRS S3 - Communautés affectées"
    assert ESRS.titre("ESRS_G1") == "ESRS G1 - Conduite des affaires"
