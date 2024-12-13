import pytest
from freezegun import freeze_time

from api.exceptions import APIError
from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from reglementations.views.base import ReglementationAction
from reglementations.views.base import ReglementationStatus
from reglementations.views.bges import BGESReglementation


ACTION_PUBLIER = ReglementationAction(
    "https://bilans-ges.ademe.fr/bilans/comment-publier",
    "Publier mon bilan GES sur la plateforme nationale",
    external=True,
)

ACTION_CONSULTER = ReglementationAction(
    "https://bilans-ges.ademe.fr/bilans",
    "Consulter les bilans GES sur la plateforme nationale",
    external=True,
)


def test_reglementation_info():
    info = BGESReglementation.info()

    assert info["title"] == "BEGES et Plan de Transition"
    assert (
        info["more_info_url"]
        == "https://portail-rse.beta.gouv.fr/fiches-reglementaires/bilan-eges-et-plan-de-transition/"
    )
    assert info["tag"] == "tag-environnement"
    assert (
        info["summary"]
        == "Mesurer ses émissions de gaz à effet de serre directes et adopter un plan de transition en conséquence."
    )


def test_est_suffisamment_qualifiee(entreprise_non_qualifiee):
    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise_non_qualifiee,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
    )

    assert BGESReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_sans_effectif(entreprise_non_qualifiee):
    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise_non_qualifiee,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
    )

    assert not BGESReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_sans_effectif_outre_mer(
    entreprise_non_qualifiee,
):
    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise_non_qualifiee,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
    )

    assert not BGESReglementation.est_suffisamment_qualifiee(caracteristiques)


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
    ],
)
def test_calcule_le_statut_si_moins_de_500_employes(
    effectif, entreprise_factory, alice, mock_api_bges
):
    entreprise = entreprise_factory(effectif=effectif)
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = BGESReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )
    assert reglementation.primary_action == ACTION_CONSULTER
    assert not mock_api_bges.called


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calcule_le_statut_si_plus_de_500_employes_sans_bilan_publie(
    effectif, entreprise_factory, alice, mock_api_bges
):
    entreprise = entreprise_factory(effectif=effectif)
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    mock_api_bges.return_value = None

    with freeze_time("2023-12-15"):
        reglementation = BGESReglementation.calculate_status(
            entreprise.dernieres_caracteristiques_qualifiantes, alice
        )

    assert reglementation.status == ReglementationStatus.STATUS_A_ACTUALISER
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 500 salariés. Vous n'avez pas encore publié votre bilan sur la plateforme Bilans GES."
    )
    assert reglementation.primary_action == ACTION_PUBLIER
    mock_api_bges.assert_called_once_with(entreprise.siren)


def test_calcule_le_statut_si_soumis_et_erreur_API(
    mocker, entreprise_factory, alice, mock_api_bges
):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    mock_api_bges.side_effect = APIError()

    with freeze_time("2023-12-15"):
        reglementation = BGESReglementation.calculate_status(
            entreprise.dernieres_caracteristiques_qualifiantes, alice
        )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 500 salariés. Suite à un problème technique, les informations concernant votre dernière publication n'ont pas pu être récupérées sur la plateforme Bilans GES. Vérifiez que vous avez publié votre bilan il y a moins de 4 ans."
    )
    assert reglementation.primary_action == ACTION_PUBLIER
    mock_api_bges.assert_called_once_with(entreprise.siren)


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calcule_le_statut_si_plus_de_500_employes_bilan_publie_trop_vieux(
    effectif, entreprise_factory, alice, mock_api_bges
):
    entreprise = entreprise_factory(effectif=effectif)
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    mock_api_bges.return_value = 2015

    with freeze_time("2023-12-15"):
        reglementation = BGESReglementation.calculate_status(
            entreprise.dernieres_caracteristiques_qualifiantes, alice
        )

    assert reglementation.status == ReglementationStatus.STATUS_A_ACTUALISER
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 500 salariés. Le dernier bilan publié sur la plateforme Bilans GES concerne l'année 2015."
    )
    assert reglementation.primary_action == ACTION_PUBLIER
    mock_api_bges.assert_called_once_with(entreprise.siren)


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calcule_le_statut_si_plus_de_500_employes_bilan_publie_recent(
    effectif, entreprise_factory, alice, mock_api_bges
):
    entreprise = entreprise_factory(effectif=effectif)
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    mock_api_bges.return_value = 2022

    with freeze_time("2023-12-15"):
        reglementation = BGESReglementation.calculate_status(
            entreprise.dernieres_caracteristiques_qualifiantes, alice
        )

    assert reglementation.status == ReglementationStatus.STATUS_A_JOUR
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 500 salariés. Vous avez publié un bilan 2022 sur la plateforme Bilans GES."
    )
    assert reglementation.primary_action == ACTION_CONSULTER
    mock_api_bges.assert_called_once_with(entreprise.siren)


def test_calcule_le_statut_avec_plus_de_250_employes_outre_mer_sans_bilan_publie(
    entreprise_factory, alice, mock_api_bges
):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_250_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    mock_api_bges.return_value = None

    with freeze_time("2023-12-15"):
        reglementation = BGESReglementation.calculate_status(
            entreprise.dernieres_caracteristiques_qualifiantes, alice
        )

    assert reglementation.status == ReglementationStatus.STATUS_A_ACTUALISER
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif outre-mer est supérieur à 250 salariés. Vous n'avez pas encore publié votre bilan sur la plateforme Bilans GES."
    )
    assert reglementation.primary_action == ACTION_PUBLIER
    mock_api_bges.assert_called_once_with(entreprise.siren)


def test_calcule_le_statut_avec_plus_de_250_employes_outre_mer_bilan_publie_trop_vieux(
    entreprise_factory, alice, mock_api_bges
):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_250_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    mock_api_bges.return_value = 2015

    with freeze_time("2023-12-15"):
        reglementation = BGESReglementation.calculate_status(
            entreprise.dernieres_caracteristiques_qualifiantes, alice
        )

    assert reglementation.status == ReglementationStatus.STATUS_A_ACTUALISER
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif outre-mer est supérieur à 250 salariés. Le dernier bilan publié sur la plateforme Bilans GES concerne l'année 2015."
    )
    assert reglementation.primary_action == ACTION_PUBLIER
    mock_api_bges.assert_called_once_with(entreprise.siren)


def test_calcule_le_statut_avec_plus_de_250_employes_outre_mer_bilan_publie_recent(
    entreprise_factory, alice, mock_api_bges
):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_250_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    mock_api_bges.return_value = 2022

    with freeze_time("2023-12-15"):
        reglementation = BGESReglementation.calculate_status(
            entreprise.dernieres_caracteristiques_qualifiantes, alice
        )

    assert reglementation.status == ReglementationStatus.STATUS_A_JOUR
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif outre-mer est supérieur à 250 salariés. Vous avez publié un bilan 2022 sur la plateforme Bilans GES."
    )
    assert reglementation.primary_action == ACTION_CONSULTER
    mock_api_bges.assert_called_once_with(entreprise.siren)


def test_publication_recente():
    annee_reporting = 2020
    with freeze_time("2023-12-15"):
        assert BGESReglementation.publication_est_recente(annee_reporting)


def test_publication_trop_ancienne():
    annee_reporting = 2020
    with freeze_time("2024-01-01"):
        assert not BGESReglementation.publication_est_recente(annee_reporting)
