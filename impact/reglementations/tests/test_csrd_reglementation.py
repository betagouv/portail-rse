import pytest
from django.urls import reverse

from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from reglementations.views.base import ReglementationStatus
from reglementations.views.csrd import CSRDReglementation


def test_reglementation_info():
    info = CSRDReglementation.info()

    assert info["title"] == "Rapport de Durabilité - CSRD"
    assert info["more_info_url"] == reverse("reglementations:fiche_csrd")
    assert info["tag"] == "tag-durabilite"
    assert info["summary"] == "Publier un rapport de durabilité"


@pytest.fixture
def _caracteristiques_suffisamment_qualifiantes_sans_groupe(entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        est_cotee=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        appartient_groupe=False,
    )
    return entreprise.dernieres_caracteristiques


@pytest.fixture
def _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        siren="000000002",
        est_cotee=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
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
        est_cotee=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    return entreprise.dernieres_caracteristiques


def test_est_suffisamment_qualifiee_sans_groupe(
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
def test_entreprise_non_cotee_bilan_et_ca_superieurs_aux_seuils_grande_entreprises_soumise_en_2026(
    bilan, ca, entreprise_factory
):
    entreprise = entreprise_factory(
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
        CSRDReglementation.est_soumis_a_partir_de(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2026
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre bilan est supérieur à 20M€",
        "votre chiffre d'affaires est supérieur à 40M€",
    ]


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_20M_ET_43M,
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
def test_entreprise_non_cotee_bilan_et_effectif_superieurs_aux_seuils_grande_entreprise_soumise_en_2026(
    bilan, effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=False,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
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
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre effectif est supérieur à 250 salariés",
        "votre bilan est supérieur à 20M€",
    ]


@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
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
def test_entreprise_non_cotee_CA_et_effectif_superieurs_aux_seuils_grande_entreprise_soumise_en_2026(
    ca, effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=False,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
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
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre effectif est supérieur à 250 salariés",
        "votre chiffre d'affaires est supérieur à 40M€",
    ]


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        CaracteristiquesAnnuelles.BILAN_ENTRE_350K_ET_6M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
    ],
)
def test_entreprise_non_cotee_bilan_et_CA_inferieurs_aux_seuils_grande_entreprise_non_soumise(
    ca, bilan, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=False,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert not CSRDReglementation.est_soumis_a_partir_de(
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
        CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
    ],
)
def test_entreprise_non_cotee_effectif_et_CA_inferieurs_aux_seuils_grande_entreprise_non_soumise(
    effectif, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=False,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=ca,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert not CSRDReglementation.est_soumis_a_partir_de(
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
        CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        CaracteristiquesAnnuelles.BILAN_ENTRE_350K_ET_6M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
    ],
)
def test_entreprise_non_cotee_effectif_et_bilan_inferieurs_aux_seuils_grande_entreprise_non_soumise(
    effectif, bilan, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=False,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert not CSRDReglementation.est_soumis_a_partir_de(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_microentreprise_cotee_car_seuil_bilan_et_ca_insuffisants_est_non_soumise(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert not CSRDReglementation.est_soumis_a_partir_de(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_microentreprise_cotee_car_seuil_effectif_et_ca_insuffisants_est_non_soumise(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert not CSRDReglementation.est_soumis_a_partir_de(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_microentreprise_cotee_car_aucun_seuil_suffisant_est_non_soumise(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert not CSRDReglementation.est_soumis_a_partir_de(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
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
def test_entreprise_cotee_ca_et_effectif_plus_de_500_superieurs_aux_seuils_grande_entreprise_soumise_en_2025(
    ca, effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=ca,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2025
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre effectif est supérieur à 500 salariés",
        "votre chiffre d'affaires est supérieur à 40M€",
    ]


@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
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
def test_entreprise_cotee_ca_et_effectif_moins_de_500_superieurs_aux_seuils_grande_entreprise_soumise_en_2026(
    ca, effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
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
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre effectif est supérieur à 250 salariés",
        "votre chiffre d'affaires est supérieur à 40M€",
    ]


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_350K_ET_6M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_20M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
    ],
)
def test_entreprise_cotee_bilan_et_ca_superieurs_aux_seuils_petite_entreprise_mais_ca_inferieur_seuil_grande_entreprise_soumise_en_2027(
    bilan, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
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
        == 2027
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre bilan est supérieur à 350k€",
        "votre chiffre d'affaires est supérieur à 700k€",
    ]


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_350K_ET_6M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
        CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
def test_entreprise_cotee_bilan_et_ca_superieurs_aux_seuils_petite_entreprise_mais_bilan_inferieur_seuil_grande_entreprise_soumise_en_2027(
    bilan, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
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
        == 2027
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre bilan est supérieur à 350k€",
        "votre chiffre d'affaires est supérieur à 700k€",
    ]


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
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
    ],
)
def test_entreprise_cotee_effectif_et_ca_superieurs_aux_seuils_petite_entreprise_mais_ca_inferieur_seuil_grande_entreprise_soumise_en_2027(
    effectif, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=ca,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2027
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre effectif est supérieur à 10 salariés",
        "votre chiffre d'affaires est supérieur à 700k€",
    ]


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
        CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
        CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
def test_entreprise_cotee_effectif_et_ca_superieurs_aux_seuils_petite_entreprise_mais_effectif_inferieur_seuil_grande_entreprise_soumise_en_2027(
    effectif, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=ca,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2027
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre effectif est supérieur à 10 salariés",
        "votre chiffre d'affaires est supérieur à 700k€",
    ]


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
@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_350K_ET_6M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
    ],
)
def test_entreprise_cotee_effectif_et_bilan_superieurs_aux_seuils_petite_entreprise_mais_bilan_inferieur_seuil_grande_entreprise_soumise_en_2027(
    effectif, bilan, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2027
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre effectif est supérieur à 10 salariés",
        "votre bilan est supérieur à 350k€",
    ]


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
        CaracteristiquesAnnuelles.BILAN_ENTRE_350K_ET_6M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_20M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
def test_entreprise_cotee_effectif_et_bilan_superieurs_aux_seuils_petite_entreprise_mais_effectif_inferieur_seuil_grande_entreprise_soumise_en_2027(
    effectif, bilan, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=False,
        effectif=effectif,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2027
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre effectif est supérieur à 10 salariés",
        "votre bilan est supérieur à 350k€",
    ]


def test_calcule_etat_si_non_soumis(entreprise_factory, alice):
    entreprise = entreprise_factory(
        est_cotee=False,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
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
    assert reglementation.primary_action.url == reverse("reglementations:csrd")


def test_calcule_etat_si_soumis_en_2027(entreprise_factory, alice):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_350K_ET_6M,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = CSRDReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation à partir de 2027 sur les données de 2026 car votre société est cotée sur un marché réglementé, votre effectif est supérieur à 10 salariés et votre bilan est supérieur à 350k€."
    )
    assert reglementation.prochaine_echeance == 2027
    assert (
        reglementation.primary_action.title
        == "Accéder à l'espace Rapport de Durabilité"
    )
    assert reglementation.primary_action.url == reverse("reglementations:csrd")


@pytest.mark.parametrize("est_cotee", [False, True])
def test_microentreprise_filiale_grand_groupe_jamais_soumise(
    est_cotee, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=est_cotee,
        appartient_groupe=True,
        est_societe_mere=False,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )


def test_microentreprise_cotee_societe_mere_grand_groupe_effectif_groupe_superieur_a_500_soumise_en_2025(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=True,
        est_societe_mere=True,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2025
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


def test_microentreprise_cotee_societe_mere_grand_groupe_effectif_groupe_inferieur_a_500_soumise_en_2026(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=True,
        est_societe_mere=True,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
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
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "votre société est la société mère d'un groupe",
        "l'effectif du groupe est supérieur à 250 salariés",
        "le bilan du groupe est supérieur à 30M€",
        "le chiffre d'affaires du groupe est supérieur à 60M€",
    ]


def test_microentreprise_non_cotee_societe_mere_grand_groupe_soumise_en_2026(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        est_cotee=False,
        appartient_groupe=True,
        est_societe_mere=True,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
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
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est la société mère d'un groupe",
        "l'effectif du groupe est supérieur à 250 salariés",
        "le bilan du groupe est supérieur à 30M€",
        "le chiffre d'affaires du groupe est supérieur à 60M€",
    ]


def test_PME_cotee_filiale_grand_groupe_effectif_groupe_superieur_a_500_soumise_en_2025(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=True,
        est_societe_mere=False,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_350K_ET_6M,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    assert (
        CSRDReglementation.est_soumis_a_partir_de(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
        == 2025
    )
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "l'effectif du groupe est supérieur à 500 salariés",
        "le bilan du groupe est supérieur à 30M€",
        "le chiffre d'affaires du groupe est supérieur à 60M€",
    ]


def test_PME_cotee_filiale_grand_groupe_effectif_groupe_inferieur_a_500_soumise_en_2026(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=True,
        est_societe_mere=False,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_350K_ET_6M,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
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
    assert CSRDReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    ) == [
        "votre société est cotée sur un marché réglementé",
        "l'effectif du groupe est supérieur à 250 salariés",
        "le bilan du groupe est supérieur à 30M€",
        "le chiffre d'affaires du groupe est supérieur à 60M€",
    ]


def test_PME_non_cotee_filiale_grand_groupe_non_soumise(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        est_cotee=False,
        appartient_groupe=True,
        est_societe_mere=False,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_350K_ET_6M,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    assert not CSRDReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
