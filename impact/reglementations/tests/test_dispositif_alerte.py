import pytest

from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import Habilitation
from reglementations.views.base import ReglementationStatus
from reglementations.views.dispositif_alerte import DispositifAlerteReglementation


def test_reglementation_info():
    info = DispositifAlerteReglementation.info()

    assert info["title"] == "Dispositif d’alerte"
    assert (
        info["more_info_url"]
        == "https://portail-rse.beta.gouv.fr/fiches-reglementaires/dispositif-dalerte/"
    )
    assert info["tag"] == "tag-gouvernance"
    assert (
        info["summary"]
        == "Avoir une procédure interne de recueil et de traitement de ces signalements."
    )
    assert info["zone"] == "france"


def test_est_suffisamment_qualifiee(entreprise_non_qualifiee):
    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise_non_qualifiee,
        effectif_securite_sociale=CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_MOINS_DE_10,
    )

    assert DispositifAlerteReglementation.est_suffisamment_qualifiee(caracteristiques)


def test_n_est_pas_suffisamment_qualifiee_car_sans_effectif(entreprise_non_qualifiee):
    caracteristiques = CaracteristiquesAnnuelles(entreprise=entreprise_non_qualifiee)

    assert not DispositifAlerteReglementation.est_suffisamment_qualifiee(
        caracteristiques
    )


@pytest.mark.parametrize(
    "effectif_securite_sociale",
    [
        CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_MOINS_DE_10,
        CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_ENTRE_10_ET_49,
    ],
)
def test_calculate_status_less_than_50_employees(
    effectif_securite_sociale, entreprise_factory, alice
):
    entreprise = entreprise_factory(effectif_securite_sociale=effectif_securite_sociale)
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")

    reglementation = DispositifAlerteReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )


@pytest.mark.parametrize(
    "effectif_securite_sociale",
    [
        CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_ENTRE_250_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_500_ET_PLUS,
    ],
)
def test_calculate_status_more_than_50_employees(
    effectif_securite_sociale, entreprise_factory, alice
):
    entreprise = entreprise_factory(effectif_securite_sociale=effectif_securite_sociale)
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")

    reglementation = DispositifAlerteReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 50 salariés."
    )
