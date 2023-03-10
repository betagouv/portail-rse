from django.urls import reverse
import pytest

from habilitations.models import add_entreprise_to_user
from reglementations.models import BDESE_50_300, BDESE_300
from reglementations.views import BDESEReglementation, ReglementationStatus


def test_bdese_reglementation_info():
    info = BDESEReglementation.info()

    assert (
        info["title"]
        == "Base de données économiques, sociales et environnementales (BDESE)"
    )
    assert (
        info["description"]
        == """L'employeur d'au moins 50 salariés doit mettre à disposition du comité économique et social (CSE) ou des représentants du personnel une base de données économiques, sociales et environnementales (BDESE).
        La BDESE rassemble les informations sur les grandes orientations économiques et sociales de l'entreprise.
        Elle comprend des mentions obligatoires qui varient selon l'effectif de l'entreprise."""
    )
    assert (
        info["more_info_url"]
        == "https://entreprendre.service-public.fr/vosdroits/F32193"
    )


@pytest.mark.parametrize("bdese_accord", [True, False])
def test_calculate_status_less_than_50_employees(bdese_accord, entreprise_factory):
    entreprise = entreprise_factory(effectif="petit", bdese_accord=bdese_accord)

    bdese = BDESEReglementation.calculate_status(entreprise, 2022)

    assert bdese.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert bdese.status_detail == "Vous n'êtes pas soumis à cette réglementation"
    assert bdese.primary_action is None
    assert bdese.secondary_actions == []

    bdese_type = BDESEReglementation.bdese_type(entreprise)
    assert bdese_type == BDESEReglementation.TYPE_NON_SOUMIS


@pytest.mark.parametrize(
    "effectif, bdese_class",
    [("moyen", BDESE_50_300), ("grand", BDESE_300), ("sup500", BDESE_300)],
)
def test_calculate_status_more_than_50_employees(
    effectif, bdese_class, entreprise_factory, mocker
):
    entreprise = entreprise_factory(effectif=effectif, bdese_accord=False)

    bdese = BDESEReglementation.calculate_status(entreprise, 2022)

    assert bdese.status == ReglementationStatus.STATUS_A_ACTUALISER
    assert (
        bdese.status_detail
        == "Vous êtes soumis à cette réglementation. Nous allons vous aider à la remplir."
    )
    assert bdese.primary_action.title == "Actualiser ma BDESE"
    assert bdese.primary_action.url == reverse(
        "bdese", args=[entreprise.siren, 2022, 0]
    )
    assert not bdese.secondary_actions

    bdese_class.objects.create(entreprise=entreprise, annee=2022)
    bdese = BDESEReglementation.calculate_status(entreprise, 2022)

    assert bdese.status == ReglementationStatus.STATUS_EN_COURS
    assert bdese.primary_action.url == reverse(
        "bdese", args=[entreprise.siren, 2022, 1]
    )
    assert (
        bdese.status_detail
        == "Vous êtes soumis à cette réglementation. Vous avez démarré le remplissage de votre BDESE sur la plateforme."
    )
    assert bdese.secondary_actions[0].title == "Télécharger le pdf (brouillon)"

    mocker.patch("reglementations.models.AbstractBDESE.is_complete", return_value=True)
    bdese = BDESEReglementation.calculate_status(entreprise, 2022)

    assert bdese.status == ReglementationStatus.STATUS_A_JOUR
    assert (
        bdese.status_detail
        == "Vous êtes soumis à cette réglementation. Vous avez actualisé votre BDESE sur la plateforme."
    )
    assert bdese.primary_action.title == "Télécharger le pdf"
    assert bdese.primary_action.url == reverse(
        "bdese_pdf", args=[entreprise.siren, 2022]
    )
    assert len(bdese.secondary_actions) == 1
    assert bdese.secondary_actions[0].title == "Modifier ma BDESE"
    assert bdese.secondary_actions[0].url == reverse(
        "bdese", args=[entreprise.siren, 2022, 1]
    )


@pytest.mark.parametrize("effectif", ["moyen", "grand", "sup500"])
def test_calculate_status_with_bdese_accord(effectif, entreprise_factory):
    entreprise = entreprise_factory(effectif=effectif, bdese_accord=True)

    bdese = BDESEReglementation.calculate_status(entreprise, 2022)

    assert bdese.status == ReglementationStatus.STATUS_A_ACTUALISER
    assert (
        bdese.status_detail
        == "Vous êtes soumis à cette réglementation. Vous avez un accord d'entreprise spécifique. Veuillez vous y référer."
    )
    assert bdese.primary_action.title == "Marquer ma BDESE comme actualisée"
    assert bdese.primary_action.url == "#"
    assert bdese.secondary_actions == []

    bdese_type = BDESEReglementation.bdese_type(entreprise)
    assert bdese_type == BDESEReglementation.TYPE_AVEC_ACCORD


def test_calculate_status_for_user(
    bdese, habilitated_user, not_habilitated_user, mocker
):
    status = BDESEReglementation.calculate_status(
        bdese.entreprise, bdese.annee, habilitated_user
    )

    assert status.status == ReglementationStatus.STATUS_EN_COURS

    status = BDESEReglementation.calculate_status(
        bdese.entreprise, bdese.annee, not_habilitated_user
    )

    assert status.status == ReglementationStatus.STATUS_A_ACTUALISER

    personal_bdese = bdese.__class__.personals.create(
        entreprise=bdese.entreprise, annee=bdese.annee, user=not_habilitated_user
    )

    status = BDESEReglementation.calculate_status(
        bdese.entreprise, bdese.annee, not_habilitated_user
    )

    assert status.status == ReglementationStatus.STATUS_EN_COURS
