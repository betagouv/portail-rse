import pytest

from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from reglementations.views.base import ReglementationStatus
from reglementations.views.dispositif_anticorruption import DispositifAntiCorruption


def test_dispositif_anticorruption_reglementation_info():
    info = DispositifAntiCorruption.info()

    assert info["title"] == "Dispositif anti-corruption"
    assert (
        info["description"]
        == """La loi dite « loi Sapin 2 » désigne la loi du 9 décembre 2016 relative à la transparence, à la lutte contre la corruption et à la modernisation de la vie économique.
        Elle impose à certaines entreprises la mise en place de mesures destinées à prévenir, détecter et sanctionner la commission, en France ou à l’étranger, de faits de corruption ou de trafic d’influence.
        Ces mesures sont diverses : code de bonne conduite, dispositif d’alerte interne, cartographie des risques, évaluation des clients et fournisseurs,
        procédures de contrôles comptables, formation du personnel exposé, régime disciplinaire propre à sanctionner les salariés en cas de violation du code de conduite,
        dispositif de contrôle et d’évaluation interne des mesures mises en œuvre."""
    )
    assert (
        info["more_info_url"]
        == "https://www.agence-francaise-anticorruption.gouv.fr/files/files/Recommandations AFA.pdf"
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
    ],
)
def test_calcule_etat_avec_effectif_insuffisant(effectif, entreprise_factory, alice):
    entreprise = entreprise_factory(
        effectif=effectif,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DispositifAntiCorruption.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
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
def test_calcule_etat_avec_ca_insuffisant(ca, entreprise_factory, alice):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        tranche_chiffre_affaires=ca,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DispositifAntiCorruption.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calcule_etat_seuils_effectif_et_ca_suffisants(
    effectif, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        effectif=effectif,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DispositifAntiCorruption.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 500 salariés et votre chiffre d'affaires est supérieur à 100 millions d'euros."
    )


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calcule_etat_seuils_effectif_et_ca_consolide_suffisants(
    effectif, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        comptes_consolides=True,
        effectif=effectif,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DispositifAntiCorruption.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 500 salariés et votre chiffre d'affaires consolidé est supérieur à 100 millions d'euros."
    )


def test_calcule_etat_seuils_effectif_ca_et_ca_consolide_suffisants(
    entreprise_factory, alice
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DispositifAntiCorruption.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 500 salariés et votre chiffre d'affaires est supérieur à 100 millions d'euros."
    )


@pytest.mark.parametrize(
    "effectif_groupe",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calcule_etat_seuils_effectif_groupe_et_ca_suffisants(
    effectif_groupe, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        societe_mere_en_france=True,
        effectif_groupe=effectif_groupe,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DispositifAntiCorruption.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car l'effectif du groupe est supérieur à 500 salariés et votre chiffre d'affaires est supérieur à 100 millions d'euros."
    )


@pytest.mark.parametrize(
    "effectif_groupe",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_calcule_etat_seuils_effectif_groupe_et_ca_suffisants_mais_siege_social_a_l_etranger(
    effectif_groupe, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        societe_mere_en_france=False,
        effectif_groupe=effectif_groupe,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = DispositifAntiCorruption.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes, alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )
