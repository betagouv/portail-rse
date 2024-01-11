import pytest
from django.urls import reverse

from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from reglementations.views.base import ReglementationStatus
from reglementations.views.dpef import DPEFReglementation


CODE_SA = 5505
CODE_SAS = 5710
CODE_SCA = 5310
CODE_SE = 5800
CODE_MUTUELLE = 8210
CODE_PREVOYANCE = 8510


def test_reglementation_info():
    info = DPEFReglementation.info()

    assert info["title"] == "Déclaration de Performance Extra-Financière"

    assert (
        info["description"]
        == """La Déclaration de Performance Extra-Financière (dite "DPEF") est un document par l'intermédiaire duquel une entreprise détaille les implications sociales, environnementales et sociétales de sa performance et de ses activités, ainsi que son mode de gouvernance."""
    )
    assert info["more_info_url"] == reverse("reglementations:fiche_dpef")


@pytest.fixture
def _caracteristiques_suffisamment_qualifiantes_sans_groupe(entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        est_cotee=False,
        effectif_permanent=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
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
        est_cotee=False,
        effectif_permanent=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
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
        effectif_permanent=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
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

    assert DPEFReglementation.est_suffisamment_qualifiee(caracteristiques)

    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides
    )

    assert DPEFReglementation.est_suffisamment_qualifiee(caracteristiques)

    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides
    )

    assert DPEFReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_est_cotee_non_renseigne(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.entreprise.est_cotee = None

    assert not DPEFReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_sans_effectif_permanent(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.effectif_permanent = None

    assert not DPEFReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_sans_CA(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.tranche_chiffre_affaires = None

    assert not DPEFReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_sans_bilan(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.tranche_bilan = None

    assert not DPEFReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_groupe_non_renseigne(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.entreprise.appartient_groupe = None

    assert not DPEFReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_groupe_mais_comptes_consolides_non_renseigne(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides,
):
    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides
    )
    caracteristiques.entreprise.comptes_consolides = None

    assert not DPEFReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_comptes_consolides_mais_sans_effectif_groupe_permanent(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides,
):
    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides
    )
    caracteristiques.effectif_groupe_permanent = None

    assert not DPEFReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_comptes_consolides_mais_sans_bilan_consolide(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides,
):
    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides
    )
    caracteristiques.tranche_bilan_consolide = None

    assert not DPEFReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_comptes_consolides_mais_sans_CA_consolide(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides,
):
    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides
    )
    caracteristiques.tranche_chiffre_affaires_consolide = None

    assert not DPEFReglementation.est_suffisamment_qualifiee(caracteristiques)


@pytest.mark.parametrize(
    "effectif_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_soumis_si_effectif_permanent_et_bilan_suffisants_et_categorie_juridique_correspondante(
    effectif_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        effectif_permanent=effectif_permanent,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        categorie_juridique_sirene=CODE_SA,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert "votre effectif permanent est supérieur à 500 salariés" in criteres_remplis
    assert "votre bilan est supérieur à 100M€" in criteres_remplis


@pytest.mark.parametrize(
    "effectif_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_soumis_si_effectif_permanent_et_ca_suffisants(
    effectif_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        effectif_permanent=effectif_permanent,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        categorie_juridique_sirene=CODE_SA,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert "votre effectif permanent est supérieur à 500 salariés" in criteres_remplis
    assert "votre chiffre d'affaires est supérieur à 100M€" in criteres_remplis


@pytest.mark.parametrize(
    "effectif_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_soumis_si_effectif_permanent_bilan_et_ca_suffisants(
    effectif_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        effectif_permanent=effectif_permanent,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        categorie_juridique_sirene=CODE_SA,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert "votre effectif permanent est supérieur à 500 salariés" in criteres_remplis
    assert "votre bilan est supérieur à 100M€" in criteres_remplis
    assert "votre chiffre d'affaires est supérieur à 100M€" in criteres_remplis


@pytest.mark.parametrize(
    "effectif_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
    ],
)
def test_non_soumis_si_effectif_permanent_insuffisant(
    effectif_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        effectif_permanent=effectif_permanent,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        categorie_juridique_sirene=CODE_SA,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert not soumis


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        CaracteristiquesAnnuelles.BILAN_ENTRE_350K_ET_6M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_20M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
        CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
    ],
)
def test_non_soumis_si_bilan_et_ca_insuffisants(bilan, ca, entreprise_factory):
    entreprise = entreprise_factory(
        effectif_permanent=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
        categorie_juridique_sirene=CODE_SA,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert not soumis


def test_non_soumis_car_certaines_categories_juridiques_sont_non_soumises(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        effectif_permanent=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        categorie_juridique_sirene=CODE_SAS,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert not soumis


@pytest.mark.parametrize(
    "categorie_juridique_sirene",
    [
        (CODE_SA, "votre entreprise est une Société Anonyme"),
        (CODE_SCA, "votre entreprise est une Société en Commandite par Actions"),
        (CODE_SE, "votre entreprise est une Société Européenne"),
    ],
)
def test_critere_categorie_juridique_si_categorie_juridique_SA_SCA_ou_SE(
    categorie_juridique_sirene, entreprise_factory
):
    entreprise = entreprise_factory(
        effectif_permanent=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        categorie_juridique_sirene=categorie_juridique_sirene[0],
    )

    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert categorie_juridique_sirene[1] in criteres_remplis


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_soumis_si_effectif_groupe_permanent_et_bilan_consolide_suffisants(
    effectif_groupe_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        categorie_juridique_sirene=CODE_SA,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert (
        "l'effectif permanent du groupe est supérieur à 500 salariés"
        in criteres_remplis
    )
    assert "votre bilan consolidé est supérieur à 100M€" in criteres_remplis


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_soumis_si_effectif_groupe_permanent_et_ca_consolide_suffisants(
    effectif_groupe_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        categorie_juridique_sirene=CODE_SA,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert (
        "l'effectif permanent du groupe est supérieur à 500 salariés"
        in criteres_remplis
    )
    assert (
        "votre chiffre d'affaires consolidé est supérieur à 100M€" in criteres_remplis
    )


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_soumis_si_effectif_groupe_permanent_bilan_et_ca_consolides_suffisants(
    effectif_groupe_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        categorie_juridique_sirene=CODE_SA,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert (
        "l'effectif permanent du groupe est supérieur à 500 salariés"
        in criteres_remplis
    )
    assert "votre bilan consolidé est supérieur à 100M€" in criteres_remplis
    assert (
        "votre chiffre d'affaires consolidé est supérieur à 100M€" in criteres_remplis
    )


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
    ],
)
def test_non_soumis_si_effectif_groupe_permanent_insuffisant(
    effectif_groupe_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        categorie_juridique_sirene=CODE_SA,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert not soumis


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_non_soumis_si_effectif_insuffisant_et_effectif_groupe_permanent_suffisant_mais_pas_de_comptes_consolides(
    effectif_groupe_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        comptes_consolides=False,
        effectif_permanent=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        categorie_juridique_sirene=CODE_SA,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert not soumis


@pytest.mark.parametrize(
    "effectif_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_20M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
def test_soumis_si_societe_cotee_et_effectif_permanent_et_bilan_suffisants(
    effectif_permanent, bilan, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        effectif_permanent=effectif_permanent,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        categorie_juridique_sirene=CODE_SA,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert "votre société est cotée sur un marché réglementé" in criteres_remplis
    assert "votre effectif permanent est supérieur à 500 salariés" in criteres_remplis
    assert "votre bilan est supérieur à 20M€" in criteres_remplis


@pytest.mark.parametrize(
    "effectif_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
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
def test_soumis_si_societe_cotee_et_effectif_permanent_et_ca_suffisants(
    effectif_permanent, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        effectif_permanent=effectif_permanent,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=ca,
        categorie_juridique_sirene=CODE_SA,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert "votre société est cotée sur un marché réglementé" in criteres_remplis
    assert "votre effectif permanent est supérieur à 500 salariés" in criteres_remplis
    assert "votre chiffre d'affaires est supérieur à 40M€" in criteres_remplis


@pytest.mark.parametrize(
    "effectif_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
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
def test_soumis_si_societe_cotee_et_effectif_permanent_bilan_et_ca_suffisants(
    effectif_permanent, bilan, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        effectif_permanent=effectif_permanent,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
        categorie_juridique_sirene=CODE_SA,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert "votre société est cotée sur un marché réglementé" in criteres_remplis
    assert "votre effectif permanent est supérieur à 500 salariés" in criteres_remplis
    assert "votre bilan est supérieur à 20M€" in criteres_remplis
    assert "votre chiffre d'affaires est supérieur à 40M€" in criteres_remplis


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_20M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
def test_soumis_si_societe_cotee_et_effectif_groupe_permanent_et_bilan_consolide_suffisants(
    effectif_groupe_permanent, bilan, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan_consolide=bilan,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        categorie_juridique_sirene=CODE_SA,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert "votre société est cotée sur un marché réglementé" in criteres_remplis
    assert (
        "l'effectif permanent du groupe est supérieur à 500 salariés"
        in criteres_remplis
    )
    assert "votre bilan consolidé est supérieur à 20M€" in criteres_remplis


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
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
def test_soumis_si_societe_cotee_et_effectif_groupe_permanent_et_ca_consolide_suffisants(
    effectif_groupe_permanent, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires_consolide=ca,
        categorie_juridique_sirene=CODE_SA,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert "votre société est cotée sur un marché réglementé" in criteres_remplis
    assert (
        "l'effectif permanent du groupe est supérieur à 500 salariés"
        in criteres_remplis
    )
    assert "votre chiffre d'affaires consolidé est supérieur à 40M€" in criteres_remplis


def test_calcule_etat_si_soumis_avec_plus_de_deux_critères_remplis(
    entreprise_factory, alice
):
    entreprise = entreprise_factory(
        est_cotee=True,
        effectif_permanent=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_20M_ET_43M,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
        categorie_juridique_sirene=CODE_SA,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DPEFReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre entreprise est une Société Anonyme, votre société est cotée sur un marché réglementé, votre effectif permanent est supérieur à 500 salariés, votre bilan est supérieur à 20M€ et votre chiffre d'affaires est supérieur à 40M€."
    )


def test_calcule_etat_si_non_soumis(entreprise_factory, alice):
    entreprise = entreprise_factory(
        est_cotee=True,
        effectif_permanent=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DPEFReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )


@pytest.mark.parametrize(
    "effectif_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_soumis_si_societe_prevoyance_et_effectif_permanent_et_bilan_suffisants(
    effectif_permanent, entreprise_factory
):
    return
    entreprise = entreprise_factory(
        est_cotee=False,
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_permanent=effectif_permanent,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        categorie_juridique_sirene=CODE_PREVOYANCE,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert "votre entreprise est une Institution de Prévoyance" in criteres_remplis
    assert "votre effectif permanent est supérieur à 500 salariés" in criteres_remplis
    assert "votre bilan est supérieur à 100M€" in criteres_remplis


@pytest.mark.parametrize(
    "effectif_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_soumis_si_societe_prevoyance_et_effectif_permanent_et_ca_suffisants(
    effectif_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=False,
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_permanent=effectif_permanent,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        categorie_juridique_sirene=CODE_PREVOYANCE,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    print(soumis)
    assert soumis
    assert "votre entreprise est une Institution de Prévoyance" in criteres_remplis
    assert "votre effectif permanent est supérieur à 500 salariés" in criteres_remplis
    assert "votre chiffre d'affaires est supérieur à 100M€" in criteres_remplis


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_soumis_si_societe_prevoyance_et_effectif_groupe_permanent_et_bilan_consolide_suffisants(
    effectif_groupe_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=False,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        categorie_juridique_sirene=CODE_PREVOYANCE,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert "votre entreprise est une Institution de Prévoyance" in criteres_remplis
    assert (
        "l'effectif permanent du groupe est supérieur à 500 salariés"
        in criteres_remplis
    )
    assert "votre bilan consolidé est supérieur à 100M€" in criteres_remplis


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_soumis_si_societe_prevoyance_et_effectif_groupe_permanent_et_ca_consolide_suffisants(
    effectif_groupe_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=False,
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        categorie_juridique_sirene=CODE_PREVOYANCE,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert "votre entreprise est une Institution de Prévoyance" in criteres_remplis
    assert (
        "l'effectif permanent du groupe est supérieur à 500 salariés"
        in criteres_remplis
    )
    assert (
        "votre chiffre d'affaires consolidé est supérieur à 100M€" in criteres_remplis
    )


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "est_cotee",
    [
        True,
        False,
    ],
)
def test_soumis_si_mutuelle_et_effectif_groupe_permanent_et_bilan_consolide_suffisants(
    effectif_groupe_permanent, est_cotee, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=est_cotee,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        categorie_juridique_sirene=CODE_MUTUELLE,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert "votre entreprise est une Mutuelle" in criteres_remplis
    assert (
        "l'effectif permanent du groupe est supérieur à 500 salariés"
        in criteres_remplis
    )
    assert "votre bilan consolidé est supérieur à 100M€" in criteres_remplis


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "est_cotee",
    [
        True,
        False,
    ],
)
def test_soumis_si_mutuelle_et_effectif_groupe_permanent_et_ca_consolide_suffisants(
    effectif_groupe_permanent, est_cotee, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=est_cotee,
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        categorie_juridique_sirene=CODE_MUTUELLE,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert "votre entreprise est une Mutuelle" in criteres_remplis
    assert (
        "l'effectif permanent du groupe est supérieur à 500 salariés"
        in criteres_remplis
    )
    assert (
        "votre chiffre d'affaires consolidé est supérieur à 100M€" in criteres_remplis
    )


def test_non_soumis_si_mutuelle_et_effectif_groupe_permanent_et_ca_consolide_insuffisants(
    entreprise_factory,
):
    """les tranches minimales de CA sont supérieures à celles du cas général"""
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
        categorie_juridique_sirene=CODE_MUTUELLE,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert not soumis
