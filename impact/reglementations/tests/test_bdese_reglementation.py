import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
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
        info["description"]
        == """L'employeur d'au moins 50 salariés doit mettre à disposition du comité économique et social (CSE) ou des représentants du personnel une base de données économiques, sociales et environnementales (BDESE).
        La BDESE rassemble les informations sur les grandes orientations économiques et sociales de l'entreprise.
        En l'absence d'accord d'entreprise spécifique, elle comprend des mentions obligatoires qui varient selon l'effectif de l'entreprise."""
    )
    assert info["more_info_url"] == reverse("reglementations:fiche_bdese")
    assert info["tag"] == "tag-social"


def test_est_suffisamment_qualifiee(entreprise_non_qualifiee):
    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise_non_qualifiee,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
    )

    assert BDESEReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_sans_effectif(entreprise_non_qualifiee):
    caracteristiques = CaracteristiquesAnnuelles(entreprise=entreprise_non_qualifiee)

    assert not BDESEReglementation.est_suffisamment_qualifiee(caracteristiques)


@pytest.mark.parametrize("est_soumis", [True, False])
def test_calculate_status_with_not_authenticated_user(
    est_soumis, entreprise_factory, mocker
):
    entreprise = entreprise_factory()
    login_url = f"{reverse('users:login')}?next={reverse('reglementations:tableau_de_bord', args=[entreprise.siren])}"

    mocker.patch(
        "reglementations.views.bdese.BDESEReglementation.est_soumis",
        return_value=est_soumis,
    )
    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, AnonymousUser()
    )

    if est_soumis:
        assert status.status == ReglementationStatus.STATUS_SOUMIS
        assert (
            status.status_detail
            == f'<a href="{login_url}">Vous êtes soumis à cette réglementation. Connectez-vous pour en savoir plus.</a>'
        )
    else:
        assert status.status == ReglementationStatus.STATUS_NON_SOUMIS
        assert status.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    assert status.primary_action is None
    assert status.secondary_actions == []


@pytest.mark.parametrize("est_soumis", [True, False])
def test_calculate_status_with_not_attached_user(
    est_soumis, entreprise_factory, alice, mocker
):
    entreprise = entreprise_factory()

    mocker.patch(
        "reglementations.views.bdese.BDESEReglementation.est_soumis",
        return_value=est_soumis,
    )
    status = BDESEReglementation.calculate_status(
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
    assert status.secondary_actions == []


@pytest.mark.parametrize("bdese_accord", [True, False])
def test_calculate_status_less_than_50_employees(
    bdese_accord, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        bdese_accord=bdese_accord,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
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
def test_calculate_status_more_than_50_employees_with_habilited_user(
    effectif, bdese_class, entreprise_factory, alice, mocker
):
    entreprise = entreprise_factory(effectif=effectif, bdese_accord=False)
    habilitation = attach_user_to_entreprise(alice, entreprise, "Présidente")
    habilitation.confirm()
    habilitation.save()
    annee = derniere_annee_a_remplir_bdese()

    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
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
        entreprise.dernieres_caracteristiques_qualifiantes, alice
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
        entreprise.dernieres_caracteristiques_qualifiantes, alice
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
def test_calculate_status_more_than_50_employees_with_not_habilited_user(
    effectif, bdese_class, entreprise_factory, alice, mocker
):
    entreprise = entreprise_factory(effectif=effectif, bdese_accord=False)
    habilitation = attach_user_to_entreprise(alice, entreprise, "Présidente")
    annee = derniere_annee_a_remplir_bdese()

    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert status.status == ReglementationStatus.STATUS_A_ACTUALISER

    bdese_class.officials.create(entreprise=entreprise, annee=annee)
    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    # L'utilisateur dont l'habilitation n'est pas confirmée voit le statut de sa BDESE personnelle, pas de celle officielle
    assert status.status == ReglementationStatus.STATUS_A_ACTUALISER

    bdese_class.personals.create(entreprise=entreprise, annee=annee, user=alice)
    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert status.status == ReglementationStatus.STATUS_EN_COURS


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
def test_calculate_status_with_bdese_accord_with_not_habilited_user(
    effectif, alice, entreprise_factory, mocker
):
    entreprise = entreprise_factory(effectif=effectif, bdese_accord=True)
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    annee = derniere_annee_a_remplir_bdese()

    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
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

    bdese = BDESEAvecAccord.officials.create(entreprise=entreprise, annee=annee)
    bdese.is_complete = True
    bdese.save()
    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    # L'utilisateur dont l'habilitation n'est pas confirmée voit le statut de sa BDESE personnelle, pas de celle officielle
    assert status.status == ReglementationStatus.STATUS_A_ACTUALISER

    bdese = BDESEAvecAccord.personals.create(
        entreprise=entreprise, annee=annee, user=alice
    )
    bdese.is_complete = True
    bdese.save()

    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert status.status == ReglementationStatus.STATUS_A_JOUR
    assert (
        status.primary_action.title == f"Marquer ma BDESE {annee} comme non actualisée"
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
def test_calculate_status_with_bdese_accord_with_habilited_user(
    effectif, alice, entreprise_factory, mocker
):
    entreprise = entreprise_factory(effectif=effectif, bdese_accord=True)
    habilitation = attach_user_to_entreprise(alice, entreprise, "Présidente")
    habilitation.confirm()
    habilitation.save()
    annee = derniere_annee_a_remplir_bdese()

    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
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

    bdese = BDESEAvecAccord.officials.create(entreprise=entreprise, annee=annee)
    bdese.is_complete = True
    bdese.save()
    status = BDESEReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert status.status == ReglementationStatus.STATUS_A_JOUR
    assert (
        status.primary_action.title == f"Marquer ma BDESE {annee} comme non actualisée"
    )
