import pytest

from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from reglementations.views.base import ReglementationStatus
from reglementations.views.plan_vigilance import PlanVigilanceReglementation

CODE_SA = 5505


def test_reglementation_info():
    info = PlanVigilanceReglementation.info()

    assert info["title"] == "Plan de vigilance"

    assert (
        info["description"]
        == """Le plan de vigilance comporte les mesures de vigilance propres à identifier et à prévenir les atteintes graves envers les droits humains et les libertés fondamentales,
        la santé et la sécurité des personnes ainsi que de l’environnement qui adviendraient au sein de l’entreprise."""
    )
    assert not info["more_info_url"]
    assert info["tag"] == "tag-social"


@pytest.fixture
def _caracteristiques_suffisamment_qualifiantes_sans_groupe(entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        categorie_juridique_sirene=CODE_SA,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        appartient_groupe=False,
    )
    return entreprise.dernieres_caracteristiques


@pytest.fixture
def _caracteristiques_suffisamment_qualifiantes_avec_groupe(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        siren="000000002",
        categorie_juridique_sirene=CODE_SA,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        appartient_groupe=True,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
    )
    return entreprise.dernieres_caracteristiques


def test_est_suffisamment_qualifiee(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
    _caracteristiques_suffisamment_qualifiantes_avec_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe

    assert PlanVigilanceReglementation.est_suffisamment_qualifiee(caracteristiques)

    caracteristiques = _caracteristiques_suffisamment_qualifiantes_avec_groupe

    assert PlanVigilanceReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_categorie_juridique_sirene_non_renseigne(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.entreprise.categorie_juridique_sirene = None

    assert not PlanVigilanceReglementation.est_suffisamment_qualifiee(caracteristiques)


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
    ],
)
@pytest.mark.parametrize(
    "effectif_groupe",
    [
        None,
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
    ],
)
def test_calcule_statut_moins_de_5000_employes(
    effectif, effectif_groupe, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        effectif=effectif,
        appartient_groupe=True if effectif_groupe else False,
        effectif_groupe=effectif_groupe,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = PlanVigilanceReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )
    assert not reglementation.primary_action


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calcule_statut_plus_de_5000_employes_dans_l_entreprise(
    effectif, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        effectif=effectif,
        categorie_juridique_sirene=CODE_SA,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = PlanVigilanceReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail.startswith(
        "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 5000 salariés."
    )
    assert reglementation.status_detail.endswith(
        "Vous devez établir un plan de vigilance si vous employez, à la clôture de deux exercices consécutifs, au moins 5 000 salariés, en votre sein ou dans vos filiales directes ou indirectes françaises, ou 10 000 salariés, en incluant vos filiales directes ou indirectes étrangères."
    )
    assert not reglementation.primary_action


@pytest.mark.parametrize(
    "effectif_groupe",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calcule_statut_plus_de_5000_employes_dans_le_groupe(
    effectif_groupe, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        appartient_groupe=True,
        effectif_groupe=effectif_groupe,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = PlanVigilanceReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail.startswith(
        "Vous êtes soumis à cette réglementation car l'effectif du groupe est supérieur à 5000 salariés."
    )
    assert reglementation.status_detail.endswith(
        "Vous devez établir un plan de vigilance si vous employez, à la clôture de deux exercices consécutifs, au moins 5 000 salariés, en votre sein ou dans vos filiales directes ou indirectes françaises, ou 10 000 salariés, en incluant vos filiales directes ou indirectes étrangères."
    )
    assert not reglementation.primary_action
