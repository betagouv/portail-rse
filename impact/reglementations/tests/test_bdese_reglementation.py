from django.urls import reverse

from reglementations.models import BDESE_300
from reglementations.views import BDESEReglementation


def test_default_bdese_reglementation():
    bdese = BDESEReglementation()

    assert (
        bdese.title
        == "Base de données économiques, sociales et environnementales (BDESE)"
    )
    assert (
        bdese.description
        == """L'employeur d'au moins 50 salariés doit mettre à disposition du comité économique et social (CSE) ou des représentants du personnel une base de données économiques, sociales et environnementales (BDESE).
        La BDESE rassemble les informations sur les grandes orientations économiques et sociales de l'entreprise.
        Elle comprend des mentions obligatoires qui varient selon l'effectif de l'entreprise."""
    )
    assert (
        bdese.more_info_url == "https://entreprendre.service-public.fr/vosdroits/F32193"
    )

    assert bdese.status is None
    assert bdese.status_detail is None
    assert bdese.primary_action is None
    assert bdese.secondary_actions == []
    assert bdese.bdese_type is None


def test_calculate_bdese_reglementation_less_than_50_employees(entreprise):
    entreprise.effectif = "petit"

    bdese = BDESEReglementation.calculate(entreprise)

    assert bdese.status == BDESEReglementation.STATUS_NON_SOUMIS
    assert bdese.status_detail == "Vous n'êtes pas soumis à cette réglementation"
    assert bdese.primary_action is None
    assert bdese.secondary_actions == []
    assert bdese.bdese_type is None


def test_calculate_bdese_reglementation_50_300_employees(entreprise):
    entreprise.effectif = "moyen"

    bdese = BDESEReglementation.calculate(entreprise)

    assert bdese.status == BDESEReglementation.STATUS_A_ACTUALISER
    assert (
        bdese.status_detail
        == "Vous êtes soumis à cette réglementation. Nous allons vous aider à la remplir."
    )
    assert bdese.primary_action.title == "Actualiser ma BDESE"
    assert bdese.primary_action.url == reverse("bdese", args=[entreprise.siren, 1])
    assert len(bdese.secondary_actions) == 1
    assert bdese.secondary_actions[0].title == "Télécharger le pdf (brouillon)"
    assert bdese.secondary_actions[0].url == reverse(
        "bdese_result", args=[entreprise.siren]
    )
    assert bdese.bdese_type is BDESEReglementation.TYPE_INFERIEUR_300


def test_calculate_bdese_reglementation_more_than_300_employees(entreprise, mocker):
    entreprise.effectif = "grand"

    bdese = BDESEReglementation.calculate(entreprise)

    assert bdese.status == BDESEReglementation.STATUS_A_ACTUALISER
    assert (
        bdese.status_detail
        == "Vous êtes soumis à cette réglementation. Nous allons vous aider à la remplir."
    )
    assert bdese.primary_action.title == "Actualiser ma BDESE"
    assert bdese.primary_action.url == reverse("bdese", args=[entreprise.siren, 1])
    assert len(bdese.secondary_actions) == 1
    assert bdese.secondary_actions[0].title == "Télécharger le pdf (brouillon)"
    assert bdese.secondary_actions[0].url == reverse(
        "bdese_result", args=[entreprise.siren]
    )
    assert bdese.bdese_type is BDESEReglementation.TYPE_INFERIEUR_500

    BDESE_300.objects.create(entreprise=entreprise)
    bdese = BDESEReglementation.calculate(entreprise)

    assert bdese.status == BDESEReglementation.STATUS_EN_COURS
    assert (
        bdese.status_detail
        == "Vous êtes soumis à cette réglementation. Vous avez démarré le remplissage de votre BDESE sur la plateforme."
    )

    mocker.patch("reglementations.models.BDESE_300.is_complete", return_value=True)
    bdese = BDESEReglementation.calculate(entreprise)

    assert bdese.status == BDESEReglementation.STATUS_ACTUALISE
    assert (
        bdese.status_detail
        == "Vous êtes soumis à cette réglementation. Vous avez actualisé votre BDESE sur la plateforme."
    )
    assert bdese.primary_action.title == "Télécharger le pdf"
    assert bdese.primary_action.url == reverse("bdese_result", args=[entreprise.siren])
    assert len(bdese.secondary_actions) == 1
    assert bdese.secondary_actions[0].title == "Modifier ma BDESE"
    assert bdese.secondary_actions[0].url == reverse(
        "bdese", args=[entreprise.siren, 1]
    )


def test_calculate_bdese_reglementation_with_bdese_accord(entreprise):
    entreprise.effectif = "moyen"
    entreprise.bdese_accord = True

    bdese = BDESEReglementation.calculate(entreprise)

    assert bdese.status == BDESEReglementation.STATUS_A_ACTUALISER
    assert (
        bdese.status_detail
        == "Vous êtes soumis à cette réglementation. Vous avez un accord d'entreprise spécifique. Veuillez vous y référer."
    )
    assert bdese.primary_action.title == "Marquer ma BDESE comme actualisée"
    assert bdese.primary_action.url == "#"
    assert bdese.secondary_actions == []
    assert bdese.bdese_type is BDESEReglementation.TYPE_AVEC_ACCORD
