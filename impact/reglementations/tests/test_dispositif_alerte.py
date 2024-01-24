import pytest
from django.urls import reverse

from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from reglementations.views.base import ReglementationStatus
from reglementations.views.dispositif_alerte import DispositifAlerteReglementation


def test_reglementation_info():
    info = DispositifAlerteReglementation.info()

    assert info["title"] == "Dispositif d’alerte"

    assert (
        info["description"]
        == "Un dispositif d’alertes professionnelles (ou DAP) est un outil permettant à une personne (salarié, cocontractant, tiers…) de porter à la connaissance d’un organisme une situation, un comportement ou un risque susceptible de caractériser une infraction ou une violation de règles éthiques adoptées par l’organisme en question, tel qu’un manquement à une charte ou à un code de conduite. Les entreprises de plus de 50 salariés doivent mettre en place depuis le 1er septembre 2022 des dispositifs d’alerte sécurisés qui garantissent la confidentialité de l’identité de l’auteur du signalement."
    )
    assert info["more_info_url"] == reverse("reglementations:fiche_dispositif_alerte")
    assert info["tag"] == "tag-gouvernance"


def test_est_suffisamment_qualifiee(entreprise_non_qualifiee):
    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise_non_qualifiee,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
    )

    assert DispositifAlerteReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_sans_effectif(entreprise_non_qualifiee):
    caracteristiques = CaracteristiquesAnnuelles(entreprise=entreprise_non_qualifiee)

    assert not DispositifAlerteReglementation.est_suffisamment_qualifiee(
        caracteristiques
    )


def test_calculate_status_less_than_50_employees(entreprise_factory, alice):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DispositifAlerteReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
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
def test_calculate_status_more_than_50_employees(effectif, entreprise_factory, alice):
    entreprise = entreprise_factory(effectif=effectif)
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DispositifAlerteReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 50 salariés."
    )
