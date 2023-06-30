import pytest

from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from reglementations.views.audit_energetique import AuditEnergetiqueReglementation
from reglementations.views.base import ReglementationStatus


def test_audit_energetique_reglementation_info():
    info = AuditEnergetiqueReglementation.info()

    assert info["title"] == "Audit énergétique"

    assert (
        info["description"]
        == "Le code de l'énergie prévoit la réalisation d’un audit énergétique pour les grandes entreprises de plus de 250 salariés, afin qu’elles mettent en place une stratégie d’efficacité énergétique de leurs activités. L’audit énergétique permet de repérer les gisements d’économies d’énergie chez les plus gros consommateurs professionnels (tertiaires et industriels). L’audit doit dater de moins de 4 ans."
    )
    assert info["more_info_url"] == ""


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
    ],
)
def test_calculate_status_less_than_50_employees(effectif, entreprise_factory, alice):
    entreprise = entreprise_factory(effectif=effectif)
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = AuditEnergetiqueReglementation(entreprise).calculate_status(
        entreprise.caracteristiques_actuelles(), alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation"
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_500_ET_PLUS,
    ],
)
def test_calculate_status_more_than_250_employees(effectif, entreprise_factory, alice):
    entreprise = entreprise_factory(effectif=effectif)
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = AuditEnergetiqueReglementation(entreprise).calculate_status(
        entreprise.caracteristiques_actuelles(), alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail == "Vous êtes soumis à cette réglementation"


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        CaracteristiquesAnnuelles.BILAN_ENTRE_350K_ET_6M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_20M_ET_43M,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
        CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
    ],
)
def test_calcule_etat_avec_bilan_et_ca_trop_faible(
    bilan, ca, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = AuditEnergetiqueReglementation(entreprise).calculate_status(
        entreprise.caracteristiques_actuelles(), alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
def test_calcule_etat_avec_bilan_et_ca_suffisants(bilan, ca, entreprise_factory, alice):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50
    )
    caracs = entreprise.caracteristiques_actuelles()
    caracs.tranche_bilan = bilan
    caracs.tranche_chiffre_affaires = ca
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = AuditEnergetiqueReglementation(entreprise).calculate_status(
        caracs, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail == "Vous êtes soumis à cette réglementation"


@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
def test_calcule_etat_avec_bilan_insuffisant(ca, entreprise_factory, alice):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50
    )
    caracs = entreprise.caracteristiques_actuelles()
    caracs.tranche_bilan = CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K
    caracs.tranche_chiffre_affaires = ca
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = AuditEnergetiqueReglementation(entreprise).calculate_status(
        caracs, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
def test_calcule_etat_avec_ca_insuffisant(bilan, entreprise_factory, alice):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50
    )
    caracs = entreprise.caracteristiques_actuelles()
    caracs.tranche_bilan = bilan
    caracs.tranche_chiffre_affaires = CaracteristiquesAnnuelles.CA_MOINS_DE_700K
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = AuditEnergetiqueReglementation(entreprise).calculate_status(
        caracs, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
