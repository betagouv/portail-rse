from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.audit_energetique import AuditEnergetiqueReglementation
from reglementations.views.base import ReglementationStatus


def test_reglementation_info():
    info = AuditEnergetiqueReglementation.info()

    assert info["title"] == "Audit énergétique"
    assert (
        info["more_info_url"]
        == "https://portail-rse.beta.gouv.fr/fiches-reglementaires/audit-energetique/"
    )
    assert info["tag"] == "tag-environnement"
    assert info["zone"] == "france"


def test_est_suffisamment_qualifiee(entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        tranche_consommation_energie_finale=CaracteristiquesAnnuelles.CONSOMMATION_ENERGIE_MOINS_DE_2_75GWH,
    )
    caracteristiques = entreprise.dernieres_caracteristiques

    assert (
        AuditEnergetiqueReglementation.est_suffisamment_qualifiee(caracteristiques)
        is True
    )


def test_n_est_pas_suffisamment_qualifiee_car_sans_tranche_energie(
    entreprise_factory,
):
    entreprise = entreprise_factory(
        siren="000000001",
        tranche_consommation_energie_finale=None,
    )
    caracteristiques = entreprise.dernieres_caracteristiques

    assert (
        AuditEnergetiqueReglementation.est_suffisamment_qualifiee(caracteristiques)
        is False
    )


def test_calcule_statut_moins_de_2_75GWH(entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        tranche_consommation_energie_finale=CaracteristiquesAnnuelles.CONSOMMATION_ENERGIE_MOINS_DE_2_75GWH,
    )

    reglementation = AuditEnergetiqueReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation."
    )
    assert not reglementation.primary_action


def test_calcule_statut_entre_2_75GWH_et_23_6GWH(entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        tranche_consommation_energie_finale=CaracteristiquesAnnuelles.CONSOMMATION_ENERGIE_ENTRE_2_75GWH_ET_23_6GWH,
    )

    reglementation = AuditEnergetiqueReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail.startswith(
        "Vous êtes soumis à cette réglementation car votre consommation énergétique est supérieure à 2,75 GWh."
    )
    assert reglementation.status_detail.endswith(
        "L'audit énergétique réglementaire est obligatoire avant le 11 octobre 2026, puis tous les 4 ans."
    )
    assert reglementation.primary_action.url == "https://audit-energie.ademe.fr/"
    assert (
        reglementation.primary_action.title
        == "Publier mon audit sur la plateforme nationale"
    )
    assert reglementation.primary_action.external


def test_calcule_statut_plus_de_23_6GWH(entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        tranche_consommation_energie_finale=CaracteristiquesAnnuelles.CONSOMMATION_ENERGIE_23_6GWH_ET_PLUS,
    )

    reglementation = AuditEnergetiqueReglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert reglementation.status_detail.startswith(
        "Vous êtes soumis à cette réglementation car votre consommation énergétique est supérieure à 2,75 GWh."
    )
    assert reglementation.status_detail.endswith(
        "Au-dessus de 23,6 GWh/an (85 TJ/an), un système de management de l'énergie certifié ISO 50001 est requis avant le 11 octobre 2027."
    )
    assert reglementation.primary_action.url == "https://audit-energie.ademe.fr/"
    assert (
        reglementation.primary_action.title
        == "Publier mon audit sur la plateforme nationale"
    )
    assert reglementation.primary_action.external
