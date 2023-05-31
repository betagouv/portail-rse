import pytest
from django.urls import reverse

from entreprises.models import Entreprise
from habilitations.models import attach_user_to_entreprise
from reglementations.models import BDESE_300
from reglementations.models import BDESE_50_300
from reglementations.models import BDESEAvecAccord
from reglementations.views import BDESEReglementation
from reglementations.views import ReglementationStatus


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
        En l'absence d'accord d'entreprise spécifique, elle comprend des mentions obligatoires qui varient selon l'effectif de l'entreprise."""
    )
    assert (
        info["more_info_url"]
        == "https://entreprendre.service-public.fr/vosdroits/F32193"
    )


@pytest.mark.parametrize("bdese_accord", [True, False])
def test_calculate_status_less_than_50_employees(
    bdese_accord, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        effectif=Entreprise.EFFECTIF_MOINS_DE_50, bdese_accord=bdese_accord
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    status = BDESEReglementation(entreprise).calculate_status(2022, alice)

    assert status.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert status.status_detail == "Vous n'êtes pas soumis à cette réglementation"
    assert status.primary_action is None
    assert status.secondary_actions == []

    bdese_type = BDESEReglementation(entreprise).bdese_type()
    assert bdese_type == BDESEReglementation.TYPE_NON_SOUMIS


@pytest.mark.parametrize(
    "effectif, bdese_class",
    [
        (Entreprise.EFFECTIF_ENTRE_50_ET_299, BDESE_50_300),
        (Entreprise.EFFECTIF_ENTRE_300_ET_499, BDESE_300),
        (Entreprise.EFFECTIF_500_ET_PLUS, BDESE_300),
    ],
)
def test_calculate_status_more_than_50_employees_with_habilited_user(
    effectif, bdese_class, entreprise_factory, alice, mocker
):
    entreprise = entreprise_factory(effectif=effectif, bdese_accord=False)
    habilitation = attach_user_to_entreprise(alice, entreprise, "Présidente")
    habilitation.confirm()
    habilitation.save()

    status = BDESEReglementation(entreprise).calculate_status(2022, alice)

    assert status.status == ReglementationStatus.STATUS_A_ACTUALISER
    assert (
        status.status_detail
        == "Vous êtes soumis à cette réglementation. Nous allons vous aider à la remplir."
    )
    assert status.primary_action.title == "Actualiser ma BDESE"
    assert status.primary_action.url == reverse(
        "reglementations:bdese", args=[entreprise.siren, 2022, 0]
    )
    assert not status.secondary_actions

    bdese_class.objects.create(entreprise=entreprise, annee=2022)
    status = BDESEReglementation(entreprise).calculate_status(2022, alice)

    assert status.status == ReglementationStatus.STATUS_EN_COURS
    assert (
        status.status_detail
        == "Vous êtes soumis à cette réglementation. Vous avez démarré le remplissage de votre BDESE 2022 sur la plateforme."
    )
    assert status.primary_action.title == "Reprendre l'actualisation de ma BDESE"
    assert status.primary_action.url == reverse(
        "reglementations:bdese", args=[entreprise.siren, 2022, 1]
    )
    assert status.secondary_actions[0].title == "Télécharger le pdf 2022 (brouillon)"

    mocker.patch("reglementations.models.AbstractBDESE.is_complete", return_value=True)
    status = BDESEReglementation(entreprise).calculate_status(2022, alice)

    assert status.status == ReglementationStatus.STATUS_A_JOUR
    assert (
        status.status_detail
        == "Vous êtes soumis à cette réglementation. Vous avez actualisé votre BDESE 2022 sur la plateforme."
    )
    assert status.primary_action.title == "Télécharger le pdf 2022"
    assert status.primary_action.url == reverse(
        "reglementations:bdese_pdf", args=[entreprise.siren, 2022]
    )
    assert len(status.secondary_actions) == 1
    assert status.secondary_actions[0].title == "Modifier ma BDESE"
    assert status.secondary_actions[0].url == reverse(
        "reglementations:bdese", args=[entreprise.siren, 2022, 1]
    )


@pytest.mark.parametrize(
    "effectif, bdese_class",
    [
        (Entreprise.EFFECTIF_ENTRE_50_ET_299, BDESE_50_300),
        (Entreprise.EFFECTIF_ENTRE_300_ET_499, BDESE_300),
        (Entreprise.EFFECTIF_500_ET_PLUS, BDESE_300),
    ],
)
def test_calculate_status_more_than_50_employees_with_not_habilited_user(
    effectif, bdese_class, entreprise_factory, alice, mocker
):
    entreprise = entreprise_factory(effectif=effectif, bdese_accord=False)
    habilitation = attach_user_to_entreprise(alice, entreprise, "Présidente")

    status = BDESEReglementation(entreprise).calculate_status(2022, alice)

    assert status.status == ReglementationStatus.STATUS_A_ACTUALISER

    bdese_class.officials.create(entreprise=entreprise, annee=2022)
    status = BDESEReglementation(entreprise).calculate_status(2022, alice)

    # L'utilisateur dont l'habilitation n'est pas confirmée voit le statut de sa BDESE personnelle, pas de celle officielle
    assert status.status == ReglementationStatus.STATUS_A_ACTUALISER

    bdese_class.personals.create(entreprise=entreprise, annee=2022, user=alice)
    status = BDESEReglementation(entreprise).calculate_status(2022, alice)

    assert status.status == ReglementationStatus.STATUS_EN_COURS


@pytest.mark.parametrize(
    "effectif",
    [
        Entreprise.EFFECTIF_ENTRE_50_ET_299,
        Entreprise.EFFECTIF_ENTRE_300_ET_499,
        Entreprise.EFFECTIF_500_ET_PLUS,
    ],
)
def test_calculate_status_with_bdese_accord_with_not_attached_user(
    effectif, alice, entreprise_factory, mocker
):
    entreprise = entreprise_factory(effectif=effectif, bdese_accord=True)

    status = BDESEReglementation(entreprise).calculate_status(2022, alice)

    assert status.status == ReglementationStatus.STATUS_SOUMIS
    assert status.status_detail == "L'entreprise est soumise à cette réglementation."
    assert not status.primary_action
    assert status.secondary_actions == []


@pytest.mark.parametrize(
    "effectif",
    [
        Entreprise.EFFECTIF_ENTRE_50_ET_299,
        Entreprise.EFFECTIF_ENTRE_300_ET_499,
        Entreprise.EFFECTIF_500_ET_PLUS,
    ],
)
def test_calculate_status_with_bdese_accord_with_not_habilited_user(
    effectif, alice, entreprise_factory, mocker
):
    entreprise = entreprise_factory(effectif=effectif, bdese_accord=True)
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    status = BDESEReglementation(entreprise).calculate_status(2022, alice)

    assert status.status == ReglementationStatus.STATUS_A_ACTUALISER
    assert (
        status.status_detail
        == "Vous êtes soumis à cette réglementation. Vous avez un accord d'entreprise spécifique. Veuillez vous y référer."
    )
    assert status.primary_action.title == "Marquer ma BDESE 2022 comme actualisée"
    assert status.primary_action.url == reverse(
        "reglementations:toggle_bdese_completion", args=[entreprise.siren, 2022]
    )
    assert status.secondary_actions == []

    bdese = BDESEAvecAccord.officials.create(entreprise=entreprise, annee=2022)
    bdese.is_complete = True
    bdese.save()
    status = BDESEReglementation(entreprise).calculate_status(2022, alice)

    assert status.status == ReglementationStatus.STATUS_A_ACTUALISER

    bdese = BDESEAvecAccord.personals.create(
        entreprise=entreprise, annee=2022, user=alice
    )
    bdese.is_complete = True
    bdese.save()

    status = BDESEReglementation(entreprise).calculate_status(2022, alice)

    assert status.status == ReglementationStatus.STATUS_A_JOUR
    assert status.primary_action.title == "Marquer ma BDESE 2022 comme non actualisée"


@pytest.mark.parametrize(
    "effectif",
    [
        Entreprise.EFFECTIF_ENTRE_50_ET_299,
        Entreprise.EFFECTIF_ENTRE_300_ET_499,
        Entreprise.EFFECTIF_500_ET_PLUS,
    ],
)
def test_calculate_status_with_bdese_accord_with_habilited_user(
    effectif, alice, entreprise_factory, mocker
):
    entreprise = entreprise_factory(effectif=effectif, bdese_accord=True)
    habilitation = attach_user_to_entreprise(alice, entreprise, "Présidente")
    habilitation.confirm()
    habilitation.save()

    status = BDESEReglementation(entreprise).calculate_status(2022, alice)

    assert status.status == ReglementationStatus.STATUS_A_ACTUALISER
    assert (
        status.status_detail
        == "Vous êtes soumis à cette réglementation. Vous avez un accord d'entreprise spécifique. Veuillez vous y référer."
    )
    assert status.primary_action.title == "Marquer ma BDESE 2022 comme actualisée"
    assert status.primary_action.url == reverse(
        "reglementations:toggle_bdese_completion", args=[entreprise.siren, 2022]
    )
    assert status.secondary_actions == []

    bdese = BDESEAvecAccord.officials.create(entreprise=entreprise, annee=2022)
    bdese.is_complete = True
    bdese.save()
    status = BDESEReglementation(entreprise).calculate_status(2022, alice)

    assert status.status == ReglementationStatus.STATUS_A_JOUR
    assert status.primary_action.title == "Marquer ma BDESE 2022 comme non actualisée"
