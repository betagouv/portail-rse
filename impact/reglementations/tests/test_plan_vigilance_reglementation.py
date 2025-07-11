import pytest

from conftest import CODE_AUTRE
from conftest import CODE_SA
from conftest import CODE_SA_COOPERATIVE
from conftest import CODE_SAS
from conftest import CODE_SCA
from conftest import CODE_SE
from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.base import ReglementationStatus
from reglementations.views.plan_vigilance import PlanVigilanceReglementation


def test_reglementation_info():
    info = PlanVigilanceReglementation.info()

    assert info["title"] == "Plan de vigilance"
    assert (
        info["more_info_url"]
        == "https://portail-rse.beta.gouv.fr/fiches-reglementaires/plan-de-vigilance/"
    )
    assert info["tag"] == "tag-gouvernance"
    assert (
        info["summary"]
        == "Établir un plan de vigilance pour prévenir des risques d’atteintes aux droits humains et à l’environnement liés à l'activité des sociétés mères et entreprises donneuses d'ordre."
    )


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
        est_societe_mere=True,
        societe_mere_en_france=True,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499,
        effectif_groupe_france=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499,
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


def test_n_est_pas_suffisamment_qualifiee_car_sans_effectif(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.effectif = None

    assert not PlanVigilanceReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_groupe_non_renseigne(
    _caracteristiques_suffisamment_qualifiantes_sans_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_sans_groupe
    caracteristiques.entreprise.appartient_groupe = None

    assert not PlanVigilanceReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_groupe_mais_societe_mere_non_renseignee(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_avec_groupe
    caracteristiques.entreprise.est_societe_mere = None

    assert not PlanVigilanceReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_groupe_mais_societe_mere_en_france_non_renseignee(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_avec_groupe
    caracteristiques.entreprise.societe_mere_en_france = None

    assert not PlanVigilanceReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_groupe_mais_sans_effectif_groupe(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_avec_groupe
    caracteristiques.effectif_groupe = None

    assert not PlanVigilanceReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_groupe_mais_sans_effectif_groupe_france(
    _caracteristiques_suffisamment_qualifiantes_avec_groupe,
):
    caracteristiques = _caracteristiques_suffisamment_qualifiantes_avec_groupe
    caracteristiques.effectif_groupe_france = None

    assert not PlanVigilanceReglementation.est_suffisamment_qualifiee(caracteristiques)


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
    ],
)
def test_calcule_statut_moins_de_5000_employes(effectif, entreprise_factory):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        effectif=effectif,
        appartient_groupe=False,
    )

    reglementation = PlanVigilanceReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )
    assert not reglementation.primary_action


@pytest.mark.parametrize(
    "effectif_groupe",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
    ],
)
def test_calcule_statut_societe_mere_francaise_moins_de_5000_employes_dans_le_groupe(
    effectif_groupe, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        appartient_groupe=True,
        est_societe_mere=True,
        societe_mere_en_france=True,
        effectif_groupe=effectif_groupe,
        effectif_groupe_france=effectif_groupe,
    )

    reglementation = PlanVigilanceReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )
    assert not reglementation.primary_action


def test_calcule_statut_autre_statut_juridique(entreprise_factory):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_AUTRE,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        appartient_groupe=False,
    )

    reglementation = PlanVigilanceReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )
    assert not reglementation.primary_action


@pytest.mark.parametrize(
    "categorie_juridique_sirene",
    [
        (CODE_SA_COOPERATIVE, "votre entreprise est une Société Anonyme"),
        (CODE_SA, "votre entreprise est une Société Anonyme"),
        (CODE_SAS, "votre entreprise est une Société par Actions Simplifiées"),
        (CODE_SCA, "votre entreprise est une Société en Commandite par Actions"),
        (CODE_SE, "votre entreprise est une Société Européenne"),
    ],
)
def test_critere_categorie_juridique_si_categorie_juridique_SA_SCA_ou_SE(
    categorie_juridique_sirene, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=categorie_juridique_sirene[0],
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    )

    reglementation = PlanVigilanceReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail.startswith(
        f"Vous êtes soumis à cette réglementation car {categorie_juridique_sirene[1]} et votre effectif est supérieur à 5 000 salariés."
    )
    assert reglementation.status_detail.endswith(
        "Vous devez établir un plan de vigilance si vous employez, à la clôture de deux exercices consécutifs, au moins 5 000 salariés, en votre sein ou dans vos filiales directes ou indirectes françaises, ou 10 000 salariés, en incluant vos filiales directes ou indirectes étrangères."
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
    effectif, entreprise_factory
):
    entreprise = entreprise_factory(
        effectif=effectif,
        categorie_juridique_sirene=CODE_SA,
    )

    reglementation = PlanVigilanceReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail.startswith(
        "Vous êtes soumis à cette réglementation car votre entreprise est une Société Anonyme et votre effectif est supérieur à 5 000 salariés."
    )
    assert reglementation.status_detail.endswith(
        "Vous devez établir un plan de vigilance si vous employez, à la clôture de deux exercices consécutifs, au moins 5 000 salariés, en votre sein ou dans vos filiales directes ou indirectes françaises, ou 10 000 salariés, en incluant vos filiales directes ou indirectes étrangères."
    )
    assert not reglementation.primary_action


@pytest.mark.parametrize(
    "effectif_groupe_france",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calcule_statut_societe_mere_francaise_plus_de_5000_employes_dans_le_groupe_france(
    effectif_groupe_france, entreprise_factory
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        appartient_groupe=True,
        est_societe_mere=True,
        societe_mere_en_france=True,
        effectif_groupe=effectif_groupe_france,
        effectif_groupe_france=effectif_groupe_france,
    )

    reglementation = PlanVigilanceReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail.startswith(
        "Vous êtes soumis à cette réglementation car votre entreprise est une Société Anonyme et l'effectif du groupe France est supérieur à 5 000 salariés."
    )
    assert reglementation.status_detail.endswith(
        "Vous devez établir un plan de vigilance si vous employez, à la clôture de deux exercices consécutifs, au moins 5 000 salariés, en votre sein ou dans vos filiales directes ou indirectes françaises, ou 10 000 salariés, en incluant vos filiales directes ou indirectes étrangères."
    )
    assert not reglementation.primary_action


@pytest.mark.parametrize(
    "effectif_groupe_france",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calcule_statut_societe_mere_etrangere_plus_de_5000_employes_dans_le_groupe_france(
    effectif_groupe_france, entreprise_factory
):
    """Cas limite
    Ce cas ne devrait pas exister car une société mère étrangère devrait avoir une catégorie juridique sirene
    de type "Personne morale de droit étranger" (comprise entre 3000 et 3999) donc différente de SA, SAS, SCA et SE
    mais un utilisateur d'une entreprise SA, SAS, SCA et SE peut remplir le formulaire de qualification en cochant la case société mère
    sans cocher la case société mère a son siège social en France. Ce cas peut donc arriver aujourd'hui.
    On considère alors que le choix de l'utilisateur prime et que la société mère est à l'étranger.
    """
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        appartient_groupe=True,
        est_societe_mere=True,
        societe_mere_en_france=False,
        effectif_groupe=effectif_groupe_france,
        effectif_groupe_france=effectif_groupe_france,
    )

    reglementation = PlanVigilanceReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )
    assert not reglementation.primary_action


def test_calcule_statut_societe_mere_francaise_moins_de_5000_employes_dans_le_groupe_france_plus_de_10000_employes_dans_le_groupe_international(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        appartient_groupe=True,
        est_societe_mere=True,
        societe_mere_en_france=True,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        effectif_groupe_france=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
    )

    reglementation = PlanVigilanceReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail.startswith(
        "Vous êtes soumis à cette réglementation car votre entreprise est une Société Anonyme et l'effectif du groupe international est supérieur à 10 000 salariés."
    )
    assert reglementation.status_detail.endswith(
        "Vous devez établir un plan de vigilance si vous employez, à la clôture de deux exercices consécutifs, au moins 5 000 salariés, en votre sein ou dans vos filiales directes ou indirectes françaises, ou 10 000 salariés, en incluant vos filiales directes ou indirectes étrangères."
    )
    assert not reglementation.primary_action


def test_calcule_statut_societe_mere_francaise_moins_de_5000_employes_dans_le_groupe_france_moins_de_10000_employes_dans_le_groupe_international(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        appartient_groupe=True,
        est_societe_mere=True,
        societe_mere_en_france=True,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        effectif_groupe_france=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
    )

    reglementation = PlanVigilanceReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )
    assert not reglementation.primary_action


def test_calcule_statut_filiale_du_groupe(entreprise_factory):
    entreprise = entreprise_factory(
        categorie_juridique_sirene=CODE_SA,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        appartient_groupe=True,
        est_societe_mere=False,  # filiale
        societe_mere_en_france=True,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        effectif_groupe_france=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    )

    reglementation = PlanVigilanceReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )
    assert not reglementation.primary_action
