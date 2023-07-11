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
def test_calcule_statut_moins_de_249_employes_et_petit_bilan(
    effectif, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        effectif=effectif, tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = AuditEnergetiqueReglementation(entreprise).calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_500_ET_PLUS,
    ],
)
def test_calcule_statut_plus_de_250_employes(effectif, entreprise_factory, alice):
    entreprise = entreprise_factory(effectif=effectif)
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = AuditEnergetiqueReglementation(entreprise).calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail.startswith(
        "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 250 salariés."
    )
    assert reglementation.status_detail.endswith(
        "Vous devez réaliser un audit énergétique si vous remplissez l'une des conditions suivantes lors des deux derniers exercices comptables : soit votre effectif est supérieur à 250 salariés, soit votre bilan est supérieur à 43M€ et votre chiffre d'affaires est supérieur à 50M€."
    )


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
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = AuditEnergetiqueReglementation(entreprise).calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
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
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = AuditEnergetiqueReglementation(entreprise).calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail.startswith(
        "Vous êtes soumis à cette réglementation car votre bilan est supérieur à 43M€ et votre chiffre d'affaires est supérieur à 50M€."
    )
    assert reglementation.status_detail.endswith(
        "Vous devez réaliser un audit énergétique si vous remplissez l'une des conditions suivantes lors des deux derniers exercices comptables : soit votre effectif est supérieur à 250 salariés, soit votre bilan est supérieur à 43M€ et votre chiffre d'affaires est supérieur à 50M€."
    )


@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
def test_calcule_etat_avec_bilan_insuffisant(ca, entreprise_factory, alice):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=ca,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = AuditEnergetiqueReglementation(entreprise).calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
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
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = AuditEnergetiqueReglementation(entreprise).calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        CaracteristiquesAnnuelles.EFFECTIF_500_ET_PLUS,
    ],
)
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
def test_calcule_etat_avec_effectif_bilan_et_ca_suffisants(
    effectif, bilan, ca, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        effectif=effectif,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = AuditEnergetiqueReglementation(entreprise).calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail.startswith(
        "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 250 salariés, votre bilan est supérieur à 43M€ et votre chiffre d'affaires est supérieur à 50M€."
    )
    assert reglementation.status_detail.endswith(
        "Vous devez réaliser un audit énergétique si vous remplissez l'une des conditions suivantes lors des deux derniers exercices comptables : soit votre effectif est supérieur à 250 salariés, soit votre bilan est supérieur à 43M€ et votre chiffre d'affaires est supérieur à 50M€."
    )


def test_calcule_etat_avec_bilan_et_ca_suffisants_mais_systeme_management_energie_en_place(
    entreprise_factory, alice
):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_500_ET_PLUS,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        systeme_management_energie=True,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = AuditEnergetiqueReglementation(entreprise).calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous n'êtes pas soumis à cette réglementation si le système de management de l'énergie est certifié par un organisme de certification accrédité par un organisme d'accréditation signataire de l'accord de reconnaissance multilatéral établi par la coordination européenne des organismes d'accréditation et que ce système prévoit un audit énergétique satisfaisant aux critères mentionnés à l'article L. 233-1."
    )
