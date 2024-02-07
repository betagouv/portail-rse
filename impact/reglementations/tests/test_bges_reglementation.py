import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from freezegun import freeze_time

from api.tests.fixtures import mock_api_bges  # noqa
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

    assert info["title"] == "BGES et plan de transition"

    assert (
        info["description"]
        == "Le bilan GES réglementaire a vocation à contribuer à la mise en œuvre de la stratégie de réduction des émissions de GES des entreprises. Un plan de transition est obligatoirement joint à ce bilan. Il vise à réduire les émissions de gaz à effet de serre et présente les objectifs, moyens et actions envisagées à cette fin ainsi que, le cas échéant, les actions mises en œuvre lors du précédent bilan. Ils sont mis à jour tous les quatre ans."
    )
    assert info["more_info_url"] == reverse("reglementations:fiche_bilan_ges")
    assert info["tag"] == "tag-environnement"


def test_est_suffisamment_qualifiee(entreprise_non_qualifiee):
    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise_non_qualifiee,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
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
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
    )

    assert not BGESReglementation.est_suffisamment_qualifiee(caracteristiques)


@pytest.mark.parametrize("est_soumis", [True, False])
def test_calculate_status_with_not_authenticated_user(
    est_soumis, entreprise_factory, mocker
):
    entreprise = entreprise_factory()
    login_url = f"{reverse('users:login')}?next={reverse('reglementations:tableau_de_bord', args=[entreprise.siren])}"

    mocker.patch(
        "reglementations.views.bges.BGESReglementation.est_soumis",
        return_value=est_soumis,
    )
    mocker.patch(
        "reglementations.views.bges.BGESReglementation.criteres_remplis",
        return_value=["RAISON"],
    )
    status = BGESReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, AnonymousUser()
    )

    if est_soumis:
        assert status.status == ReglementationStatus.STATUS_SOUMIS
        assert (
            status.status_detail
            == f'<a href="{login_url}">Vous êtes soumis à cette réglementation si RAISON. Connectez-vous pour en savoir plus.</a>'
        )
    else:
        assert status.status == ReglementationStatus.STATUS_NON_SOUMIS
        assert status.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    assert status.primary_action == ACTION_CONSULTER
    assert status.secondary_actions == []


@pytest.mark.parametrize("est_soumis", [True, False])
def test_calculate_status_with_not_attached_user(
    est_soumis, entreprise_factory, alice, mocker
):
    entreprise = entreprise_factory()

    mocker.patch(
        "reglementations.views.bges.BGESReglementation.est_soumis",
        return_value=est_soumis,
    )
    status = BGESReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    if est_soumis:
        assert status.status == ReglementationStatus.STATUS_SOUMIS
        assert (
            status.status_detail == "L'entreprise est soumise à cette réglementation."
        )
    else:
        assert status.status == ReglementationStatus.STATUS_NON_SOUMIS
        assert (
            status.status_detail
            == "L'entreprise n'est pas soumise à cette réglementation."
        )
    assert status.primary_action is None
    assert status.secondary_actions == []


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
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
