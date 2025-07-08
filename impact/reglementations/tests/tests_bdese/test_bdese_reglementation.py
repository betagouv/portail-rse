import pytest
from django.urls import reverse

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.models import BDESE_300
from reglementations.models import BDESE_50_300
from reglementations.models import BDESEAvecAccord
from reglementations.models import derniere_annee_a_remplir_bdese
from reglementations.views.base import ReglementationStatus
from reglementations.views.bdese import BDESEReglementation


def test_reglementation_info():
    info = BDESEReglementation.info()

    assert (
        info["title"]
        == "Base de données économiques, sociales et environnementales (BDESE)"
    )
    assert (
        info["more_info_url"]
        == "https://portail-rse.beta.gouv.fr/fiches-reglementaires/base-de-donnees-economiques-sociales-et-environnementales/"
    )
    assert info["tag"] == "tag-social"
    assert (
        info["summary"]
        == "Constituer une base de données économiques, sociales et environnementales à transmettre à son CSE."
    )
    assert info["zone"] == "france"


def test_est_suffisamment_qualifiee(entreprise_non_qualifiee):
    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise_non_qualifiee,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
    )

    assert BDESEReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_sans_effectif(entreprise_non_qualifiee):
    caracteristiques = CaracteristiquesAnnuelles(entreprise=entreprise_non_qualifiee)

    assert not BDESEReglementation.est_suffisamment_qualifiee(caracteristiques)


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
    ],
)
@pytest.mark.parametrize("bdese_accord", [True, False])
def test_calculate_status_less_than_50_employees(
    effectif, bdese_accord, entreprise_factory
):
    entreprise = entreprise_factory(
        effectif=effectif,
        bdese_accord=bdese_accord,
    )

    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert status.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert status.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    assert status.primary_action.title == "Tester une BDESE"
    annee = derniere_annee_a_remplir_bdese()
    assert status.primary_action.url == reverse(
        "reglementations:bdese_step", args=[entreprise.siren, annee, 1]
    )
    assert status.secondary_actions == []


@pytest.mark.parametrize(
    "effectif, bdese_class",
    [
        (CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249, BDESE_50_300),
        (CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299, BDESE_50_300),
        (CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499, BDESE_300),
        (CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999, BDESE_300),
        (CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999, BDESE_300),
        (CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS, BDESE_300),
    ],
)
def test_calculate_status_more_than_50_employees(
    effectif, bdese_class, entreprise_factory, mocker
):
    entreprise = entreprise_factory(effectif=effectif, bdese_accord=False)
    annee = derniere_annee_a_remplir_bdese()

    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert status.status == ReglementationStatus.STATUS_A_ACTUALISER
    assert (
        status.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 50 salariés. Nous allons vous aider à la remplir."
    )
    assert status.primary_action.title == "Actualiser ma BDESE"
    assert status.primary_action.url == reverse(
        "reglementations:bdese_step", args=[entreprise.siren, annee, 0]
    )
    assert not status.secondary_actions

    bdese_class.objects.create(entreprise=entreprise, annee=annee)
    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert status.status == ReglementationStatus.STATUS_EN_COURS
    assert (
        status.status_detail
        == f"Vous êtes soumis à cette réglementation car votre effectif est supérieur à 50 salariés. Vous avez démarré le remplissage de votre BDESE {annee} sur la plateforme."
    )
    assert status.primary_action.title == "Reprendre l'actualisation de ma BDESE"
    assert status.primary_action.url == reverse(
        "reglementations:bdese_step", args=[entreprise.siren, annee, 1]
    )
    assert (
        status.secondary_actions[0].title == f"Télécharger le pdf {annee} (brouillon)"
    )

    mocker.patch("reglementations.models.AbstractBDESE.is_complete", return_value=True)
    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert status.status == ReglementationStatus.STATUS_A_JOUR
    assert (
        status.status_detail
        == f"Vous êtes soumis à cette réglementation car votre effectif est supérieur à 50 salariés. Vous avez actualisé votre BDESE {annee} sur la plateforme."
    )
    assert status.primary_action.title == f"Télécharger le pdf {annee}"
    assert status.primary_action.url == reverse(
        "reglementations:bdese_pdf", args=[entreprise.siren, annee]
    )
    assert len(status.secondary_actions) == 1
    assert status.secondary_actions[0].title == "Modifier ma BDESE"
    assert status.secondary_actions[0].url == reverse(
        "reglementations:bdese_step", args=[entreprise.siren, annee, 1]
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calculate_status_with_bdese_accord(effectif, entreprise_factory, mocker):
    entreprise = entreprise_factory(effectif=effectif, bdese_accord=True)
    annee = derniere_annee_a_remplir_bdese()

    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert status.status == ReglementationStatus.STATUS_A_ACTUALISER
    assert (
        status.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 50 salariés. Vous avez un accord d'entreprise spécifique. Veuillez vous y référer."
    )
    assert status.primary_action.title == f"Marquer ma BDESE {annee} comme actualisée"
    assert status.primary_action.url == reverse(
        "reglementations:toggle_bdese_completion", args=[entreprise.siren, annee]
    )
    assert status.secondary_actions == []

    bdese = BDESEAvecAccord.objects.create(entreprise=entreprise, annee=annee)
    bdese.is_complete = True
    bdese.save()
    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert status.status == ReglementationStatus.STATUS_A_JOUR
    assert (
        status.primary_action.title == f"Marquer ma BDESE {annee} comme non actualisée"
    )
