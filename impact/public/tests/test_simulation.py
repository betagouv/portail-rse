import html
from datetime import date
from datetime import timedelta

import pytest
from django.conf import settings
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

import api.exceptions
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from habilitations.models import Habilitation
from public.views import should_commit
from reglementations.views.audit_energetique import AuditEnergetiqueReglementation
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.bges import BGESReglementation
from reglementations.views.csrd import CSRDReglementation
from reglementations.views.dispositif_alerte import DispositifAlerteReglementation
from reglementations.views.dispositif_anticorruption import DispositifAntiCorruption
from reglementations.views.index_egapro import IndexEgaproReglementation
from reglementations.views.plan_vigilance import PlanVigilanceReglementation

REGLEMENTATIONS = (
    CSRDReglementation,
    BDESEReglementation,
    IndexEgaproReglementation,
    DispositifAlerteReglementation,
    BGESReglementation,
    AuditEnergetiqueReglementation,
    DispositifAntiCorruption,
    PlanVigilanceReglementation,
)

CODE_PAYS_SUEDE = 99104
from conftest import CODE_PAYS_PORTUGAL


@pytest.fixture
def entreprise(db, alice, entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        denomination="Entreprise SAS",
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
    )
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    return entreprise


@pytest.mark.parametrize("status_est_soumis", [True, False])
@pytest.mark.django_db
def test_premiere_simulation_sur_entreprise_inexistante_en_bdd(
    status_est_soumis, client, mocker
):
    siren = "000000001"
    denomination = "Entreprise SAS"
    categorie_juridique_sirene = 5200
    code_pays_etranger_sirene = ""  # France
    code_NAF = "01.11Z"
    effectif = CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10
    ca = CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M
    bilan = CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M
    est_cotee = True
    appartient_groupe = True
    est_societe_mere = True
    effectif_groupe = CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    comptes_consolides = True
    ca_consolide = CaracteristiquesAnnuelles.CA_100M_ET_PLUS
    bilan_consolide = CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS

    data = {
        "siren": siren,
        "denomination": denomination,
        "categorie_juridique_sirene": categorie_juridique_sirene,
        "code_pays_etranger_sirene": code_pays_etranger_sirene,
        "code_NAF": code_NAF,
        "effectif": effectif,
        "tranche_chiffre_affaires": ca,
        "tranche_bilan": bilan,
        "est_cotee": est_cotee,
        "appartient_groupe": appartient_groupe,
        "est_societe_mere": est_societe_mere,
        "effectif_groupe": effectif_groupe,
        "comptes_consolides": comptes_consolides,
        "tranche_chiffre_affaires_consolide": ca_consolide,
        "tranche_bilan_consolide": bilan_consolide,
    }

    for REGLEMENTATION in REGLEMENTATIONS:
        mock_est_soumis = mocker.patch(
            f"{REGLEMENTATION.__module__}.{REGLEMENTATION.__name__}.est_soumis",
            return_value=status_est_soumis,
        )

    response = client.post("/simulation", data=data, follow=True)

    # l'entreprise a été créée avec les caractéristiques de simulation
    entreprise = Entreprise.objects.get(siren=siren)
    assert entreprise.denomination == denomination
    assert entreprise.categorie_juridique_sirene == categorie_juridique_sirene
    assert entreprise.code_pays_etranger_sirene is None
    assert entreprise.code_NAF == "01.11Z"
    assert entreprise.est_cotee
    assert entreprise.appartient_groupe
    assert entreprise.est_societe_mere
    assert entreprise.comptes_consolides
    caracteristiques = entreprise.caracteristiques_actuelles()
    assert caracteristiques.effectif == effectif
    assert caracteristiques.effectif_groupe == effectif_groupe
    assert caracteristiques.tranche_chiffre_affaires == ca
    assert caracteristiques.tranche_bilan == bilan
    assert caracteristiques.tranche_chiffre_affaires_consolide == ca_consolide
    assert caracteristiques.tranche_bilan_consolide == bilan_consolide

    # les caractéristiques non présentes dans la simulation simplifiées sont laissées vides en base
    assert entreprise.date_cloture_exercice is None
    assert entreprise.est_interet_public is None
    assert entreprise.societe_mere_en_france is None
    assert caracteristiques.effectif_outre_mer is None
    assert caracteristiques.effectif_groupe_france is None
    assert caracteristiques.bdese_accord is None
    assert caracteristiques.systeme_management_energie is None

    # les données servant à la simulation sont celles du formulaire de simulation simplifiée
    # enrichies avec des valeurs par défaut pour les champs manquants
    simulation_caracs = mock_est_soumis.call_args.args[0]
    assert simulation_caracs.date_cloture_exercice.month == 12
    assert simulation_caracs.date_cloture_exercice.day == 31
    assert simulation_caracs.entreprise.est_interet_public is False
    assert simulation_caracs.entreprise.societe_mere_en_france
    assert (
        simulation_caracs.effectif_outre_mer
        == CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250
    )
    assert simulation_caracs.effectif_groupe_france == effectif_groupe
    assert not simulation_caracs.bdese_accord
    assert not simulation_caracs.systeme_management_energie

    # les réglementations applicables sont affichées sur la page de résultat
    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("resultats_simulation"), 302)]

    context = response.context
    reglementations_applicables = context["reglementations_applicables"]
    if status_est_soumis:
        assert len(reglementations_applicables) == len(REGLEMENTATIONS)
    else:
        assert not reglementations_applicables

    content = response.content.decode("utf-8")
    for reglementation in reglementations_applicables:
        assert reglementation.title in content
    assert "<!-- page resultats simulation -->" in content


@pytest.mark.parametrize("status_est_soumis", [True, False])
@pytest.mark.django_db
def test_formulaire_prerempli_avec_la_simulation_précédente(status_est_soumis, client):
    siren = "000000001"
    denomination = "Entreprise SAS"
    categorie_juridique_sirene = 5200
    code_pays_etranger_sirene = ""  # France
    code_NAF = "01.11Z"
    effectif = CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10
    ca = CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M
    bilan = CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M
    est_cotee = True
    appartient_groupe = True
    est_societe_mere = True
    effectif_groupe = CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    comptes_consolides = True
    ca_consolide = CaracteristiquesAnnuelles.CA_100M_ET_PLUS
    bilan_consolide = CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS

    data = {
        "siren": siren,
        "denomination": denomination,
        "categorie_juridique_sirene": categorie_juridique_sirene,
        "code_pays_etranger_sirene": code_pays_etranger_sirene,
        "code_NAF": code_NAF,
        "effectif": effectif,
        "tranche_chiffre_affaires": ca,
        "tranche_bilan": bilan,
        "est_cotee": est_cotee,
        "appartient_groupe": appartient_groupe,
        "est_societe_mere": est_societe_mere,
        "effectif_groupe": effectif_groupe,
        "comptes_consolides": comptes_consolides,
        "tranche_chiffre_affaires_consolide": ca_consolide,
        "tranche_bilan_consolide": bilan_consolide,
    }

    response = client.post("/simulation", data=data)
    response = client.get("/simulation")

    # le formulaire est toujours sur la page, avec les bonnes données d'initialisation
    simulation_form = response.context["form"]
    assert simulation_form["siren"].value() == siren
    assert simulation_form["denomination"].value() == denomination
    assert (
        simulation_form["categorie_juridique_sirene"].value()
        == categorie_juridique_sirene
    )
    assert simulation_form["code_NAF"].value() == code_NAF
    assert simulation_form["effectif"].value() == effectif
    assert simulation_form["tranche_chiffre_affaires"].value() == ca
    assert simulation_form["tranche_bilan"].value() == bilan
    assert simulation_form["est_cotee"].value() == est_cotee
    assert simulation_form["appartient_groupe"].value() == appartient_groupe
    assert simulation_form["est_societe_mere"].value() == est_societe_mere
    assert simulation_form["effectif_groupe"].value() == effectif_groupe
    assert simulation_form["comptes_consolides"].value() == comptes_consolides
    assert simulation_form["tranche_chiffre_affaires_consolide"].value() == ca_consolide
    assert simulation_form["tranche_bilan_consolide"].value() == bilan_consolide


@pytest.mark.django_db
@pytest.mark.skipif(
    settings.OIDC_ENABLED,
    reason="Test non pertinent avec OIDC activé - le formulaire de création classique n'est pas disponible",
)
def test_formulaire_creation_compte_prerempli_avec_le_siren_de_la_simulation_précédente(
    client,
):
    siren = "000000001"
    denomination = "Entreprise SAS"
    data = {
        "siren": siren,
        "denomination": "Entreprise SAS",
        "categorie_juridique_sirene": 5200,
        "code_pays_etranger_sirene": "",
        "code_NAF": "01.11Z",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        "est_cotee": False,
        "appartient_groupe": False,
    }

    client.post("/simulation", data=data)
    response = client.get("/creation")

    creation_form = response.context["form"]
    assert creation_form["siren"].value() == siren
    content = response.content.decode("utf-8")
    assert siren in content
    assert denomination in content


@pytest.mark.parametrize("status_est_soumis", [True, False])
def test_simulation_par_un_utilisateur_authentifie_sur_une_nouvelle_entreprise(
    status_est_soumis, client, entreprise, mocker
):
    """
    Ce cas est encore accessible mais ne correspond pas à un parcours utilisateur normal
    """
    client.force_login(entreprise.users.first())

    data = {
        "denomination": "Une autre entreprise SAS",
        "siren": "000000002",
        "categorie_juridique_sirene": 5200,
        "code_pays_etranger_sirene": CODE_PAYS_PORTUGAL,
        "code_NAF": "01.11Z",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        "est_cotée": False,
        "appartient_groupe": True,
        "est_societe_mere": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    }

    for REGLEMENTATION in REGLEMENTATIONS:
        mock_est_soumis = mocker.patch(
            f"{REGLEMENTATION.__module__}.{REGLEMENTATION.__name__}.est_soumis",
            return_value=status_est_soumis,
        )

    response = client.post("/simulation", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("resultats_simulation"), 302)]


def test_lors_d_une_simulation_les_donnees_d_une_entreprise_avec_des_caracteristiques_actuelles_ne_sont_pas_modifiees(
    client, entreprise_factory, mocker
):
    """
    La simulation sur une entreprise déjà enregistrée en base avec des caracteristiques actuelles ne modifie pas ses caractéristiques
    mais calcule quand même les résultats correspondant aux données utilisées lors de la simulation
    """
    date_cloture_dernier_exercice = date.today() - timedelta(days=1)
    entreprise = entreprise_factory(
        date_cloture_exercice=date_cloture_dernier_exercice,
        categorie_juridique_sirene=5200,
        code_pays_etranger_sirene=CODE_PAYS_PORTUGAL,
        code_NAF="01.11Z",
        est_cotee=True,
        appartient_groupe=True,
        est_societe_mere=True,
        societe_mere_en_france=True,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_250_ET_PLUS,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_MOINS_DE_60M,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_MOINS_DE_30M,
        bdese_accord=True,
        systeme_management_energie=True,
    )

    autre_effectif = CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    autre_ca = CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M
    autre_bilan = CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M
    autre_denomination = "Autre dénomination"
    autre_categorie_juridique_sirene = 5300
    autre_code_pays_etranger_sirene = CODE_PAYS_SUEDE
    autre_code_NAF = "99.00Z"
    data = {
        "siren": entreprise.siren,
        "denomination": autre_denomination,
        "categorie_juridique_sirene": autre_categorie_juridique_sirene,
        "code_pays_etranger_sirene": autre_code_pays_etranger_sirene,
        "code_NAF": autre_code_NAF,
        "effectif": autre_effectif,
        "tranche_chiffre_affaires": autre_ca,
        "tranche_bilan": autre_bilan,
        "est_cotee": False,
        "appartient_groupe": False,
    }

    mock_est_soumis = mocker.patch(
        "reglementations.views.base.Reglementation.est_soumis"
    )

    response = client.post("/simulation", data=data, follow=True)

    entreprise.refresh_from_db()
    assert entreprise.date_cloture_exercice == date_cloture_dernier_exercice
    assert entreprise.categorie_juridique_sirene == 5200
    assert entreprise.code_NAF == "01.11Z"
    assert entreprise.est_cotee
    assert entreprise.appartient_groupe
    assert entreprise.est_societe_mere
    assert entreprise.societe_mere_en_france
    assert entreprise.comptes_consolides
    caracteristiques = entreprise.caracteristiques_annuelles(
        entreprise.date_cloture_exercice.year
    )
    assert (
        caracteristiques.effectif == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499
    )
    assert (
        caracteristiques.effectif_groupe
        == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    assert (
        caracteristiques.tranche_chiffre_affaires
        == CaracteristiquesAnnuelles.CA_MOINS_DE_900K
    )
    assert (
        caracteristiques.tranche_bilan == CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K
    )
    assert (
        caracteristiques.tranche_chiffre_affaires_consolide
        == CaracteristiquesAnnuelles.CA_MOINS_DE_60M
    )
    assert (
        caracteristiques.tranche_bilan_consolide
        == CaracteristiquesAnnuelles.BILAN_MOINS_DE_30M
    )
    assert caracteristiques.bdese_accord
    assert caracteristiques.systeme_management_energie

    assert mock_est_soumis.called
    caracteristiques_simulees = mock_est_soumis.call_args.args[0]
    assert caracteristiques_simulees.entreprise.siren == data["siren"]
    assert caracteristiques_simulees.entreprise.denomination == data["denomination"]
    assert (
        caracteristiques_simulees.entreprise.categorie_juridique_sirene
        == data["categorie_juridique_sirene"]
    )
    assert (
        caracteristiques_simulees.entreprise.code_pays_etranger_sirene
        == data["code_pays_etranger_sirene"]
    )
    assert caracteristiques_simulees.effectif == data["effectif"]
    assert (
        caracteristiques_simulees.tranche_chiffre_affaires
        == data["tranche_chiffre_affaires"]
    )
    assert caracteristiques_simulees.tranche_bilan == data["tranche_bilan"]
    assert caracteristiques_simulees.entreprise.est_cotee == data["est_cotee"]
    assert (
        caracteristiques_simulees.entreprise.appartient_groupe
        == data["appartient_groupe"]
    )


def test_lors_d_une_simulation_les_donnees_d_une_entreprise_avec_utilisateur_ne_sont_pas_modifiees(
    client, alice, entreprise_non_qualifiee, mocker
):
    """
    La simulation sur une entreprise déjà enregistrée en base avec un utilisateur ne crée pas de caractéristique
    mais calcule quand même les résultats correspondant aux données utilisées lors de la simulation
    """

    entreprise = entreprise_non_qualifiee
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")

    effectif = CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    effectif_groupe = CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    ca = CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M
    bilan = CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M
    ca_consolide = CaracteristiquesAnnuelles.CA_100M_ET_PLUS
    bilan_consolide = CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS
    autre_denomination = "Autre dénomination"
    autre_categorie_juridique_sirene = 5200
    autre_code_pays_etranger_sirene = CODE_PAYS_SUEDE
    autre_code_NAF = "99.00Z"
    data = {
        "siren": entreprise.siren,
        "denomination": autre_denomination,
        "categorie_juridique_sirene": autre_categorie_juridique_sirene,
        "code_pays_etranger_sirene": autre_code_pays_etranger_sirene,
        "code_NAF": autre_code_NAF,
        "effectif": effectif,
        "tranche_chiffre_affaires": ca,
        "tranche_bilan": bilan,
        "est_cotee": True,
        "appartient_groupe": True,
        "est_societe_mere": True,
        "effectif_groupe": effectif_groupe,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": ca_consolide,
        "tranche_bilan_consolide": bilan_consolide,
    }

    mock_est_soumis = mocker.patch(
        "reglementations.views.base.Reglementation.est_soumis"
    )

    response = client.post("/simulation", data=data, follow=True)

    entreprise.refresh_from_db()
    assert entreprise.date_cloture_exercice is None
    assert entreprise.categorie_juridique_sirene != autre_categorie_juridique_sirene
    assert entreprise.code_pays_etranger_sirene != autre_code_pays_etranger_sirene
    assert entreprise.code_NAF != autre_code_NAF
    assert entreprise.est_cotee is None
    assert entreprise.appartient_groupe is None
    assert entreprise.est_societe_mere is None
    assert entreprise.comptes_consolides is None
    assert not entreprise.caracteristiques_actuelles()

    assert mock_est_soumis.called
    caracteristiques_simulees = mock_est_soumis.call_args.args[0]
    assert caracteristiques_simulees.entreprise.siren == data["siren"]
    assert caracteristiques_simulees.entreprise.denomination == data["denomination"]
    assert (
        caracteristiques_simulees.entreprise.categorie_juridique_sirene
        == data["categorie_juridique_sirene"]
    )
    assert (
        caracteristiques_simulees.entreprise.code_pays_etranger_sirene
        == data["code_pays_etranger_sirene"]
    )
    assert caracteristiques_simulees.effectif == data["effectif"]
    assert (
        caracteristiques_simulees.tranche_chiffre_affaires
        == data["tranche_chiffre_affaires"]
    )
    assert caracteristiques_simulees.tranche_bilan == data["tranche_bilan"]
    assert caracteristiques_simulees.entreprise.est_cotee == data["est_cotee"]
    assert (
        caracteristiques_simulees.entreprise.appartient_groupe
        == data["appartient_groupe"]
    )
    assert (
        caracteristiques_simulees.entreprise.est_societe_mere
        == data["est_societe_mere"]
    )
    assert caracteristiques_simulees.effectif_groupe == data["effectif_groupe"]
    assert (
        caracteristiques_simulees.entreprise.comptes_consolides
        == data["comptes_consolides"]
    )
    assert (
        caracteristiques_simulees.tranche_chiffre_affaires_consolide
        == data["tranche_chiffre_affaires_consolide"]
    )
    assert (
        caracteristiques_simulees.tranche_bilan_consolide
        == data["tranche_bilan_consolide"]
    )


def test_lors_d_une_simulation_les_donnees_d_une_entreprise_sans_caracteristiques_actuelles_sont_enregistrees(
    client, entreprise_non_qualifiee, mocker
):
    """
    La simulation sur une entreprise déjà enregistrée en base sans caracteristiques actuelles enregistre les données de simulation
    et calcule les résultats correspondant aux données utilisées lors de la simulation
    """

    entreprise = entreprise_non_qualifiee

    effectif = CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    effectif_groupe = CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    ca = CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M
    bilan = CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M
    ca_consolide = CaracteristiquesAnnuelles.CA_100M_ET_PLUS
    bilan_consolide = CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS
    autre_denomination = "Autre dénomination"
    autre_categorie_juridique_sirene = 5200
    autre_code_pays_etranger_sirene = CODE_PAYS_PORTUGAL
    autre_code_NAF = "99.00Z"
    data = {
        "denomination": autre_denomination,
        "siren": entreprise.siren,
        "categorie_juridique_sirene": autre_categorie_juridique_sirene,
        "code_pays_etranger_sirene": autre_code_pays_etranger_sirene,
        "code_NAF": autre_code_NAF,
        "effectif": effectif,
        "tranche_chiffre_affaires": ca,
        "tranche_bilan": bilan,
        "est_cotee": True,
        "appartient_groupe": True,
        "est_societe_mere": True,
        "effectif_groupe": effectif_groupe,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": ca_consolide,
        "tranche_bilan_consolide": bilan_consolide,
    }

    mock_est_soumis = mocker.patch(
        "reglementations.views.base.Reglementation.est_soumis"
    )

    response = client.post("/simulation", data=data, follow=True)

    entreprise.refresh_from_db()
    assert entreprise.date_cloture_exercice is None
    assert entreprise.denomination == autre_denomination
    assert entreprise.categorie_juridique_sirene == autre_categorie_juridique_sirene
    assert entreprise.code_pays_etranger_sirene == autre_code_pays_etranger_sirene
    assert entreprise.code_NAF == autre_code_NAF
    assert entreprise.est_cotee
    assert entreprise.appartient_groupe
    assert entreprise.est_societe_mere
    assert entreprise.comptes_consolides
    caracteristiques = entreprise.caracteristiques_actuelles()
    assert caracteristiques.effectif == effectif
    assert caracteristiques.effectif_groupe == effectif_groupe
    assert caracteristiques.tranche_chiffre_affaires == ca
    assert caracteristiques.tranche_bilan == bilan
    assert caracteristiques.tranche_chiffre_affaires_consolide == ca_consolide
    assert caracteristiques.tranche_bilan_consolide == bilan_consolide

    assert mock_est_soumis.called
    caracteristiques_simulees = mock_est_soumis.call_args.args[0]
    assert caracteristiques_simulees.entreprise.siren == data["siren"]
    assert caracteristiques_simulees.entreprise.denomination == data["denomination"]
    assert (
        caracteristiques_simulees.entreprise.categorie_juridique_sirene
        == data["categorie_juridique_sirene"]
    )
    assert (
        caracteristiques_simulees.entreprise.code_pays_etranger_sirene
        == data["code_pays_etranger_sirene"]
    )
    assert caracteristiques_simulees.effectif == data["effectif"]
    assert (
        caracteristiques_simulees.tranche_chiffre_affaires
        == data["tranche_chiffre_affaires"]
    )
    assert caracteristiques_simulees.tranche_bilan == data["tranche_bilan"]
    assert caracteristiques_simulees.entreprise.est_cotee == data["est_cotee"]
    assert (
        caracteristiques_simulees.entreprise.appartient_groupe
        == data["appartient_groupe"]
    )
    assert (
        caracteristiques_simulees.entreprise.est_societe_mere
        == data["est_societe_mere"]
    )
    assert caracteristiques_simulees.effectif_groupe == data["effectif_groupe"]
    assert (
        caracteristiques_simulees.entreprise.comptes_consolides
        == data["comptes_consolides"]
    )
    assert (
        caracteristiques_simulees.tranche_chiffre_affaires_consolide
        == data["tranche_chiffre_affaires_consolide"]
    )
    assert (
        caracteristiques_simulees.tranche_bilan_consolide
        == data["tranche_bilan_consolide"]
    )


def test_should_not_commit_une_entreprise_avec_des_caracteristiques_actuelles_sans_utilisateur(
    client, entreprise_factory
):
    date_cloture_dernier_exercice = date.today() - timedelta(days=1)
    entreprise = entreprise_factory(date_cloture_exercice=date_cloture_dernier_exercice)
    assert entreprise.caracteristiques_actuelles()

    # une simulation ne devrait jamais écraser des caractéristiques existantes
    assert not should_commit(entreprise)


def test_should_not_commit_une_entreprise_avec_des_caracteristiques_actuelles_avec_utilisateur(
    client, entreprise_factory, alice
):
    date_cloture_dernier_exercice = date.today() - timedelta(days=1)
    entreprise = entreprise_factory(date_cloture_exercice=date_cloture_dernier_exercice)
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")

    assert entreprise.caracteristiques_actuelles()

    # une simulation ne devrait jamais écraser des caractéristiques existantes
    assert not should_commit(entreprise)


def test_should_commit_une_entreprise_sans_caracteristiques_actuelles_sans_utilisateur(
    client, entreprise_non_qualifiee, alice
):
    entreprise = entreprise_non_qualifiee
    assert not entreprise.users.all()
    assert not entreprise.caracteristiques_actuelles()

    assert should_commit(entreprise)


def test_should_not_commit_une_entreprise_sans_caracteristiques_actuelles_avec_utilisateur(
    client, entreprise_non_qualifiee, alice
):
    entreprise = entreprise_non_qualifiee
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")

    assert not should_commit(entreprise)


@pytest.mark.django_db
def test_simulation_incorrecte(client):
    invalid_data = {
        "denomination": "Entreprise SAS",
        "siren": "000000001",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        "appartient_groupe": True,
        "comptes_consolides": True,
    }

    response = client.post("/simulation", data=invalid_data)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Impossible de finaliser la simulation car le formulaire contient des erreurs."
        in content
    )

    assert Entreprise.objects.count() == 0
    assert CaracteristiquesAnnuelles.objects.count() == 0


@pytest.mark.django_db
def test_simulation_en_session_incorrecte(client):
    """
    Ce cas peut arriver si les champs de la simulation évoluent. Des données précédemment correctes ne le sont plus.
    """
    invalid_data = {
        "siren": "000000001",
        "denomination": "Entreprise SAS",
        "categorie_juridique_sirene": 5200,
        "effectif": "0-19",  # Cette valeur n'existe pas
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        "est_cotee": False,
        "appartient_groupe": False,
    }

    session = client.session
    session["simulation"] = invalid_data
    session.save()

    response = client.get("/simulation")

    assert response.status_code == 200

    # le formulaire n'est pas initialisé
    context = response.context
    simulation_form = context["form"]
    assert not simulation_form["siren"].value()


@pytest.mark.django_db
def test_pas_de_résultats_de_la_simulation_après_une_déconnexion(client):
    """
    La déconnexion vide le contenu de la session donc les données de simulation sont absentes.
    """
    response = client.get("/simulation/resultats", follow=True)

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "<!-- page simulation -->" in content


def test_preremplissage_simulation(client, mock_api_infos_entreprise):
    siren = "123456789"
    infos_entreprise = mock_api_infos_entreprise.return_value

    response = client.get(
        "/simulation/fragments/preremplissage-formulaire-simulation",
        query_params={"siren": siren},
    )

    mock_api_infos_entreprise.assert_called_once_with(siren, donnees_financieres=True)
    assert response.status_code == 200
    assertTemplateUsed(response, "fragments/simulation_form.html")
    context = response.context
    assert not context["erreur_recherche_entreprise"]
    # le formulaire est prérempli les données d'API
    simulation_form = response.context["form"]
    assert simulation_form["siren"].value() == infos_entreprise["siren"]
    assert simulation_form["denomination"].value() == infos_entreprise["denomination"]
    assert (
        simulation_form["categorie_juridique_sirene"].value()
        == infos_entreprise["categorie_juridique_sirene"]
    )
    assert simulation_form["code_NAF"].value() == infos_entreprise["code_NAF"]
    assert simulation_form["effectif"].value() == infos_entreprise["effectif"]
    assert (
        simulation_form["tranche_chiffre_affaires"].value()
        == infos_entreprise["tranche_chiffre_affaires"]
    )
    assert (
        simulation_form["appartient_groupe"].value()
        == infos_entreprise["appartient_groupe"]
    )
    assert (
        simulation_form["comptes_consolides"].value()
        == infos_entreprise["comptes_consolides"]
    )
    assert (
        simulation_form["tranche_chiffre_affaires_consolide"].value()
        == infos_entreprise["tranche_chiffre_affaires_consolide"]
    )


def test_preremplissage_simulation_erreur_API(client, mock_api_infos_entreprise):
    siren = "123456789"
    mock_api_infos_entreprise.side_effect = api.exceptions.APIError("Panne serveur")

    response = client.get(
        "/simulation/fragments/preremplissage-formulaire-simulation",
        query_params={"siren": siren},
    )

    assert response.status_code == 200
    context = response.context
    assert context["erreur_recherche_entreprise"] == "Panne serveur"
    content = response.content.decode("utf-8")
    assert "Panne serveur" in content


def test_preremplissage_simulation_avec_entreprise_test(
    client, mock_api_infos_entreprise
):
    siren = settings.SIREN_ENTREPRISE_TEST

    response = client.get(
        "/simulation/fragments/preremplissage-formulaire-simulation",
        query_params={"siren": siren},
    )

    assert not mock_api_infos_entreprise.called
    assert response.status_code == 200
    context = response.context
    assert not context["erreur_recherche_entreprise"]
    # le formulaire est prérempli avec des données de test
    simulation_form = response.context["form"]
    assert simulation_form["siren"].value() == settings.SIREN_ENTREPRISE_TEST
    assert simulation_form["denomination"].value() == "ENTREPRISE TEST"
    assert simulation_form["categorie_juridique_sirene"].value() == 5505
    assert simulation_form["code_NAF"].value() == "01.11Z"
    assert (
        simulation_form["effectif"].value()
        == CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    )
    assert (
        simulation_form["tranche_chiffre_affaires"].value()
        == CaracteristiquesAnnuelles.CA_100M_ET_PLUS
    )
    assert (
        simulation_form["tranche_bilan"].value()
        == CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS
    )
    assert not simulation_form["appartient_groupe"].value()
