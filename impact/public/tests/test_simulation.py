import html
from datetime import date
from datetime import timedelta

import pytest
from django.contrib.auth.models import AnonymousUser

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from habilitations.models import attach_user_to_entreprise
from public.views import should_commit
from reglementations.views.audit_energetique import AuditEnergetiqueReglementation
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.bges import BGESReglementation
from reglementations.views.dispositif_alerte import DispositifAlerteReglementation
from reglementations.views.dispositif_anticorruption import DispositifAntiCorruption
from reglementations.views.dpef import DPEFReglementation
from reglementations.views.index_egapro import IndexEgaproReglementation
from reglementations.views.plan_vigilance import PlanVigilanceReglementation

REGLEMENTATIONS = (
    BDESEReglementation,
    IndexEgaproReglementation,
    DispositifAlerteReglementation,
    BGESReglementation,
    AuditEnergetiqueReglementation,
    DispositifAntiCorruption,
    DPEFReglementation,
    PlanVigilanceReglementation,
)


@pytest.fixture
def entreprise(db, alice, entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        denomination="Entreprise SAS",
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    return entreprise


@pytest.mark.parametrize("status_est_soumis", [True, False])
@pytest.mark.django_db
def test_premiere_simulation_sur_entreprise_inexistante_en_bdd(
    status_est_soumis, client, mocker
):
    siren = "000000001"
    denomination = "Entreprise SAS"
    categorie_juridique_sirene = 5200
    effectif = CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50
    ca = CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M
    bilan = CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M
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
    assert entreprise.societe_mere_en_france is None
    assert caracteristiques.effectif_permanent is None
    assert caracteristiques.effectif_outre_mer is None
    assert caracteristiques.effectif_groupe_france is None
    assert caracteristiques.effectif_groupe_permanent is None
    assert caracteristiques.bdese_accord is None
    assert caracteristiques.systeme_management_energie is None

    # les données servant à la simulation sont celles du formulaire de simulation simplifiée
    # enrichies avec des valeurs par défaut pour les champs manquants
    simulation_caracs = mock_est_soumis.call_args.args[0]
    assert simulation_caracs.entreprise.societe_mere_en_france
    assert simulation_caracs.effectif_permanent == effectif
    assert (
        simulation_caracs.effectif_outre_mer
        == CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250
    )
    assert simulation_caracs.effectif_groupe_france == effectif_groupe
    assert simulation_caracs.effectif_groupe_permanent == effectif_groupe
    assert not simulation_caracs.bdese_accord
    assert not simulation_caracs.systeme_management_energie

    # les statuts des réglementations de cette entreprise sont affichées de manière anonyme (non détaillée)
    # car l'utilisateur n'est pas authentifié
    context = response.context
    reglementations = context["reglementations"]
    for index, REGLEMENTATION in enumerate(REGLEMENTATIONS):
        assert reglementations[index]["status"] == REGLEMENTATION.calculate_status(
            simulation_caracs, AnonymousUser()
        )

    content = response.content.decode("utf-8")
    if status_est_soumis:
        assert (
            '<p class="fr-badge fr-badge--info fr-badge--no-icon">' in content
        ), content
        anonymous_status_detail = "Vous êtes soumis à cette réglementation si "
        assert anonymous_status_detail in content, content
        assert '<p class="fr-badge">non soumis</p>' not in content, content
    else:
        assert '<p class="fr-badge">non soumis</p>' in content, content
        anonymous_status_detail = "Vous n'êtes pas soumis à cette réglementation."
        assert anonymous_status_detail in content, content
        assert (
            '<p class="fr-badge fr-badge--info fr-badge--no-icon">' not in content
        ), content

    # le formulaire est toujours sur la page, avec les bonnes données d'initialisation
    simulation_form = context["simulation_form"]
    assert simulation_form["siren"].value() == siren
    assert simulation_form["denomination"].value() == denomination
    assert (
        simulation_form["categorie_juridique_sirene"].value()
        == categorie_juridique_sirene
    )
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
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "est_cotée": False,
        "appartient_groupe": True,
        "est_societe_mere": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
    }

    for REGLEMENTATION in REGLEMENTATIONS:
        mock_est_soumis = mocker.patch(
            f"{REGLEMENTATION.__module__}.{REGLEMENTATION.__name__}.est_soumis",
            return_value=status_est_soumis,
        )

    response = client.post("/simulation", data=data, follow=True)

    content = response.content.decode("utf-8")
    reglementations = response.context["reglementations"]
    if status_est_soumis:
        assert '<p class="fr-badge fr-badge--info fr-badge--no-icon">' in content
        anonymous_status_detail = "L'entreprise est soumise à cette réglementation."
        assert anonymous_status_detail in content, content
    else:
        assert '<p class="fr-badge">non soumis</p>' in content
        anonymous_status_detail = (
            "L'entreprise n'est pas soumise à cette réglementation."
        )
        assert anonymous_status_detail in content, content


def test_lors_d_une_simulation_les_donnees_d_une_entreprise_avec_des_caracteristiques_actuelles_ne_sont_pas_modifiees(
    client, entreprise_factory
):
    """
    La simulation sur une entreprise déjà enregistrée en base avec des caracteristiques actuelles ne modifie pas ses caractéristiques
    mais affiche quand même les statuts correspondant aux données utilisées lors de la simulation
    """
    date_cloture_dernier_exercice = date.today() - timedelta(days=1)
    entreprise = entreprise_factory(
        date_cloture_exercice=date_cloture_dernier_exercice,
        categorie_juridique_sirene=5200,
        est_cotee=True,
        appartient_groupe=True,
        est_societe_mere=True,
        societe_mere_en_france=True,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_250_ET_PLUS,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        bdese_accord=True,
        systeme_management_energie=True,
    )
    assert entreprise.caracteristiques_actuelles()

    effectif = CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    ca = CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M
    bilan = CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M
    autre_denomination = "Autre dénomination"
    autre_categorie_juridique_sirene = 5300

    data = {
        "siren": entreprise.siren,
        "denomination": autre_denomination,
        "categorie_juridique_sirene": autre_categorie_juridique_sirene,
        "effectif": effectif,
        "tranche_chiffre_affaires": ca,
        "tranche_bilan": bilan,
        "est_cotee": False,
        "appartient_groupe": False,
    }

    response = client.post("/simulation", data=data, follow=True)

    entreprise.refresh_from_db()
    assert entreprise.date_cloture_exercice == date_cloture_dernier_exercice
    assert entreprise.categorie_juridique_sirene == 5200
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
        == CaracteristiquesAnnuelles.CA_MOINS_DE_700K
    )
    assert (
        caracteristiques.tranche_bilan == CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K
    )
    assert (
        caracteristiques.tranche_chiffre_affaires_consolide
        == CaracteristiquesAnnuelles.CA_MOINS_DE_700K
    )
    assert (
        caracteristiques.tranche_bilan_consolide
        == CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K
    )
    assert caracteristiques.bdese_accord
    assert caracteristiques.systeme_management_energie

    context = response.context
    reglementations = context["reglementations"]
    entreprise_simulee = Entreprise(
        siren=entreprise.siren,
        categorie_juridique_sirene=autre_categorie_juridique_sirene,
        est_cotee=False,
        appartient_groupe=False,
    )
    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise_simulee,
        effectif=effectif,
        effectif_permanent=effectif,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        tranche_chiffre_affaires=ca,
        tranche_bilan=bilan,
        bdese_accord=False,
        systeme_management_energie=False,
    )
    for index, REGLEMENTATION in enumerate(REGLEMENTATIONS):
        status = reglementations[index]["status"]
        assert status == REGLEMENTATION.calculate_status(
            caracteristiques, AnonymousUser()
        ), REGLEMENTATION


def test_lors_d_une_simulation_les_donnees_d_une_entreprise_avec_utilisateur_ne_sont_pas_modifiees(
    client, alice, entreprise_non_qualifiee
):
    """
    La simulation sur une entreprise déjà enregistrée en base avec un utilisateur ne crée pas de caractéristique
    mais affiche quand même les statuts correspondant aux données utilisées lors de la simulation
    """

    entreprise = entreprise_non_qualifiee
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    effectif = CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    effectif_groupe = CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    ca = CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M
    bilan = CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M
    autre_denomination = "Autre dénomination"
    autre_categorie_juridique_sirene = 5200

    data = {
        "siren": entreprise.siren,
        "denomination": autre_denomination,
        "categorie_juridique_sirene": autre_categorie_juridique_sirene,
        "effectif": effectif,
        "tranche_chiffre_affaires": ca,
        "tranche_bilan": bilan,
        "est_cotee": True,
        "appartient_groupe": True,
        "est_societe_mere": True,
        "effectif_groupe": effectif_groupe,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": ca,
        "tranche_bilan_consolide": bilan,
    }

    response = client.post("/simulation", data=data, follow=True)

    entreprise.refresh_from_db()
    assert entreprise.date_cloture_exercice is None
    assert entreprise.categorie_juridique_sirene != autre_categorie_juridique_sirene
    assert entreprise.est_cotee is None
    assert entreprise.appartient_groupe is None
    assert entreprise.est_societe_mere is None
    assert entreprise.comptes_consolides is None
    assert not entreprise.caracteristiques_actuelles()

    context = response.context
    reglementations = context["reglementations"]
    entreprise_simulee = Entreprise(
        siren=entreprise.siren,
        categorie_juridique_sirene=autre_categorie_juridique_sirene,
        est_cotee=True,
        appartient_groupe=True,
        est_societe_mere=True,
        societe_mere_en_france=True,
        comptes_consolides=True,
    )
    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise_simulee,
        effectif=effectif,
        effectif_permanent=effectif,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        effectif_groupe=effectif_groupe,
        effectif_groupe_france=effectif_groupe,
        effectif_groupe_permanent=effectif_groupe,
        tranche_chiffre_affaires=ca,
        tranche_bilan=bilan,
        tranche_chiffre_affaires_consolide=ca,
        tranche_bilan_consolide=bilan,
        bdese_accord=False,
        systeme_management_energie=False,
    )
    for index, REGLEMENTATION in enumerate(REGLEMENTATIONS):
        status = reglementations[index]["status"]
        assert status == REGLEMENTATION.calculate_status(
            caracteristiques, AnonymousUser()
        )


def test_lors_d_une_simulation_les_donnees_d_une_entreprise_sans_caracteristiques_actuelles_sont_enregistrees(
    client, entreprise_non_qualifiee
):
    """
    La simulation sur une entreprise déjà enregistrée en base sans caracteristiques actuelles enregistre les données de simulation
    et affiche les statuts correspondant aux données utilisées lors de la simulation
    """

    entreprise = entreprise_non_qualifiee

    effectif = CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    effectif_groupe = CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    ca = CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M
    bilan = CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M
    autre_denomination = "Autre dénomination"
    autre_categorie_juridique_sirene = 5200
    data = {
        "denomination": autre_denomination,
        "siren": entreprise.siren,
        "categorie_juridique_sirene": autre_categorie_juridique_sirene,
        "effectif": effectif,
        "tranche_chiffre_affaires": ca,
        "tranche_bilan": bilan,
        "est_cotee": True,
        "appartient_groupe": True,
        "est_societe_mere": True,
        "effectif_groupe": effectif_groupe,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": ca,
        "tranche_bilan_consolide": bilan,
    }

    response = client.post("/simulation", data=data, follow=True)

    entreprise.refresh_from_db()
    assert entreprise.date_cloture_exercice is None
    assert entreprise.denomination == autre_denomination
    assert entreprise.categorie_juridique_sirene == autre_categorie_juridique_sirene
    assert entreprise.est_cotee
    assert entreprise.appartient_groupe
    assert entreprise.est_societe_mere
    assert entreprise.comptes_consolides
    caracteristiques = entreprise.caracteristiques_actuelles()
    assert caracteristiques.effectif == effectif
    assert caracteristiques.effectif_groupe == effectif_groupe
    assert caracteristiques.tranche_chiffre_affaires == ca
    assert caracteristiques.tranche_bilan == bilan
    assert caracteristiques.tranche_chiffre_affaires_consolide == ca
    assert caracteristiques.tranche_bilan_consolide == bilan

    context = response.context
    reglementations = context["reglementations"]
    entreprise_simulee = Entreprise(
        siren=entreprise.siren,
        categorie_juridique_sirene=autre_categorie_juridique_sirene,
        est_cotee=True,
        appartient_groupe=True,
        est_societe_mere=True,
        societe_mere_en_france=True,
        comptes_consolides=True,
    )
    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise_simulee,
        effectif=effectif,
        effectif_permanent=effectif,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        effectif_groupe=effectif_groupe,
        effectif_groupe_france=effectif_groupe,
        effectif_groupe_permanent=effectif_groupe,
        tranche_chiffre_affaires=ca,
        tranche_bilan=bilan,
        tranche_chiffre_affaires_consolide=ca,
        tranche_bilan_consolide=bilan,
        bdese_accord=False,
        systeme_management_energie=False,
    )
    for index, REGLEMENTATION in enumerate(REGLEMENTATIONS):
        status = reglementations[index]["status"]
        assert status == REGLEMENTATION.calculate_status(
            caracteristiques, AnonymousUser()
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
    attach_user_to_entreprise(alice, entreprise, "Présidente")

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
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    assert not should_commit(entreprise)


@pytest.mark.django_db
def test_simulation_incorrecte(client):
    unvalid_data = {
        "denomination": "Entreprise SAS",
        "siren": "000000001",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "appartient_groupe": True,
        "comptes_consolides": True,
    }

    response = client.post("/simulation", data=unvalid_data)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Impossible de finaliser la simulation car le formulaire contient des erreurs."
        in content
    )

    assert Entreprise.objects.count() == 0
    assert CaracteristiquesAnnuelles.objects.count() == 0
