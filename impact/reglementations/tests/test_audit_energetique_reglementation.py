import pytest

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.audit_energetique import AuditEnergetiqueReglementation
from reglementations.views.base import ReglementationStatus


def test_reglementation_info():
    info = AuditEnergetiqueReglementation.info()

    assert info["title"] == "Audit énergétique"
    assert (
        info["more_info_url"]
        == "https://portail-rse.beta.gouv.fr/fiches-reglementaires/audit-energetique/"
    )
    assert info["tag"] == "tag-environnement"
    assert info["zone"] == "france"


@pytest.fixture
def _caracteristiques_suffisamment_qualifiantes_sans_groupe(entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        systeme_management_energie=True,
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
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        systeme_management_energie=True,
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
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        systeme_management_energie=True,
        appartient_groupe=True,
        comptes_consolides=True,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_MOINS_DE_30M,
    )
    return entreprise.dernieres_caracteristiques


def test_est_suffisamment_qualifiee(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides,
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe

    assert (
        AuditEnergetiqueReglementation.est_suffisamment_qualifiee(caracteristiques)
        is True
    )

    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides
    )

    assert (
        AuditEnergetiqueReglementation.est_suffisamment_qualifiee(caracteristiques)
        is True
    )

    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides
    )

    assert (
        AuditEnergetiqueReglementation.est_suffisamment_qualifiee(caracteristiques)
        is True
    )


def test_n_est_pas_suffisamment_qualifiee_car_sans_effectif(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.effectif = None

    assert (
        AuditEnergetiqueReglementation.est_suffisamment_qualifiee(caracteristiques)
        is False
    )


def test_n_est_pas_suffisamment_qualifiee_car_sans_ca(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.tranche_chiffre_affaires = None

    assert (
        AuditEnergetiqueReglementation.est_suffisamment_qualifiee(caracteristiques)
        is False
    )


def test_n_est_pas_suffisamment_qualifiee_car_sans_bilan(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.tranche_bilan = None

    assert (
        AuditEnergetiqueReglementation.est_suffisamment_qualifiee(caracteristiques)
        is False
    )


def test_n_est_pas_suffisamment_qualifiee_car_groupe_non_renseigne(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.entreprise.appartient_groupe = None

    assert (
        AuditEnergetiqueReglementation.est_suffisamment_qualifiee(caracteristiques)
        is False
    )


def test_n_est_pas_suffisamment_qualifiee_car_sysmteme_management_non_renseigne(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.systeme_management_energie = None

    assert (
        AuditEnergetiqueReglementation.est_suffisamment_qualifiee(caracteristiques)
        is False
    )


def test_n_est_pas_suffisamment_qualifiee_car_groupe_mais_comptes_consolides_non_renseigne(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides,
):

    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_sans_comptes_consolides
    )
    caracteristiques.entreprise.comptes_consolides = None

    assert (
        AuditEnergetiqueReglementation.est_suffisamment_qualifiee(caracteristiques)
        is False
    )


def test_n_est_pas_suffisamment_qualifiee_car_groupe_mais_bilan_consolide_non_renseigne(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides,
):
    caracteristiques = (
        _caracteristiques_suffisamment_qualifiantes_avec_groupe_et_comptes_consolides
    )
    caracteristiques.tranche_bilan_consolide = None

    assert (
        AuditEnergetiqueReglementation.est_suffisamment_qualifiee(caracteristiques)
        is False
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
    ],
)
def test_calcule_statut_moins_de_249_employes_et_petit_bilan(
    effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        effectif=effectif, tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K
    )

    reglementation = AuditEnergetiqueReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )
    assert not reglementation.primary_action


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
def test_calcule_statut_plus_de_250_employes(effectif, entreprise_factory):
    entreprise = entreprise_factory(effectif=effectif)

    reglementation = AuditEnergetiqueReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail.startswith(
        "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 250 salariés."
    )
    assert reglementation.status_detail.endswith(
        "Vous devez réaliser un audit énergétique si vous remplissez l'une des conditions suivantes lors des deux derniers exercices comptables : soit votre effectif est supérieur à 250 salariés, soit votre bilan (ou bilan consolidé) est supérieur à 43M€ et votre chiffre d'affaires est supérieur à 50M€."
    )
    assert reglementation.primary_action.url == "https://audit-energie.ademe.fr/"
    assert (
        reglementation.primary_action.title
        == "Publier mon audit sur la plateforme nationale"
    )
    assert reglementation.primary_action.external


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_25M_ET_43M,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
    ],
)
def test_calcule_etat_avec_bilan_et_ca_trop_faible(bilan, ca, entreprise_factory):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
    )

    reglementation = AuditEnergetiqueReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert not reglementation.primary_action


@pytest.mark.parametrize(
    "bilan",
    [
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
def test_calcule_etat_avec_bilan_et_ca_suffisants(bilan, ca, entreprise_factory):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
    )

    reglementation = AuditEnergetiqueReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail.startswith(
        "Vous êtes soumis à cette réglementation car votre bilan est supérieur à 43M€ et votre chiffre d'affaires est supérieur à 50M€."
    )
    assert reglementation.status_detail.endswith(
        "Vous devez réaliser un audit énergétique si vous remplissez l'une des conditions suivantes lors des deux derniers exercices comptables : soit votre effectif est supérieur à 250 salariés, soit votre bilan (ou bilan consolidé) est supérieur à 43M€ et votre chiffre d'affaires est supérieur à 50M€."
    )
    assert reglementation.primary_action.url == "https://audit-energie.ademe.fr/"
    assert (
        reglementation.primary_action.title
        == "Publier mon audit sur la plateforme nationale"
    )
    assert reglementation.primary_action.external


@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
def test_calcule_etat_avec_bilan_insuffisant(ca, entreprise_factory):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=ca,
    )

    reglementation = AuditEnergetiqueReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert not reglementation.primary_action


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
def test_calcule_etat_avec_ca_insuffisant(bilan, entreprise_factory):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
    )

    reglementation = AuditEnergetiqueReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert not reglementation.primary_action


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
@pytest.mark.parametrize(
    "bilan",
    [
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
def test_calcule_etat_avec_effectif_bilan_et_ca_suffisants(
    effectif, bilan, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        effectif=effectif,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
    )

    reglementation = AuditEnergetiqueReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail.startswith(
        "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 250 salariés, votre bilan est supérieur à 43M€ et votre chiffre d'affaires est supérieur à 50M€."
    )
    assert reglementation.status_detail.endswith(
        "Vous devez réaliser un audit énergétique si vous remplissez l'une des conditions suivantes lors des deux derniers exercices comptables : soit votre effectif est supérieur à 250 salariés, soit votre bilan (ou bilan consolidé) est supérieur à 43M€ et votre chiffre d'affaires est supérieur à 50M€."
    )
    assert reglementation.primary_action.url == "https://audit-energie.ademe.fr/"
    assert (
        reglementation.primary_action.title
        == "Publier mon audit sur la plateforme nationale"
    )
    assert reglementation.primary_action.external


def test_calcule_etat_avec_bilan_et_ca_suffisants_mais_systeme_management_energie_en_place(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        systeme_management_energie=True,
    )

    reglementation = AuditEnergetiqueReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous n'êtes pas soumis à cette réglementation si le système de management de l'énergie est certifié conforme à la norme ISO 50001."
    )
    assert not reglementation.primary_action


@pytest.mark.parametrize(
    "bilan_consolide",
    [
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
def test_calcule_etat_avec_bilan_insuffisant_mais_bilan_consolide_et_ca_suffisants(
    bilan_consolide, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires=ca,
        tranche_bilan_consolide=bilan_consolide,
    )

    reglementation = AuditEnergetiqueReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail.startswith(
        "Vous êtes soumis à cette réglementation car votre bilan consolidé est supérieur à 43M€ et votre chiffre d'affaires est supérieur à 50M€."
    )
    assert reglementation.status_detail.endswith(
        "Vous devez réaliser un audit énergétique si vous remplissez l'une des conditions suivantes lors des deux derniers exercices comptables : soit votre effectif est supérieur à 250 salariés, soit votre bilan (ou bilan consolidé) est supérieur à 43M€ et votre chiffre d'affaires est supérieur à 50M€."
    )
    assert reglementation.primary_action.url == "https://audit-energie.ademe.fr/"
    assert (
        reglementation.primary_action.title
        == "Publier mon audit sur la plateforme nationale"
    )
    assert reglementation.primary_action.external
