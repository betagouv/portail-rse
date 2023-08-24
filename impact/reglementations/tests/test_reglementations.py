import html
from datetime import timedelta

import pytest
from django.contrib.auth.models import AnonymousUser
from freezegun import freeze_time

from api.tests.fixtures import mock_api_recherche_entreprises  # noqa
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from habilitations.models import attach_user_to_entreprise
from reglementations.views import should_commit
from reglementations.views.audit_energetique import AuditEnergetiqueReglementation
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.bges import BGESReglementation
from reglementations.views.dispositif_alerte import DispositifAlerteReglementation
from reglementations.views.index_egapro import IndexEgaproReglementation


REGLEMENTATIONS = (
    BDESEReglementation,
    IndexEgaproReglementation,
    DispositifAlerteReglementation,
    BGESReglementation,
    AuditEnergetiqueReglementation,
)


def test_page_publique_des_reglementations(client):
    response = client.get("/reglementations")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "<!-- page reglementations -->" in content
    assert "BDESE" in content
    assert "Index de l’égalité professionnelle" in content

    context = response.context
    assert context["entreprise"] is None
    for index, REGLEMENTATION in enumerate(REGLEMENTATIONS):
        assert context["reglementations"][index]["info"] == REGLEMENTATION.info()
        assert context["reglementations"][index]["status"] is None


def test_page_reglementations_redirige_utilisateur_authentifie_vers_les_reglementations_associees_a_son_entreprise(
    client, entreprise
):
    client.force_login(entreprise.users.first())

    response = client.get("/reglementations", follow=True)

    assert response.status_code == 200

    url = f"/reglementations/{entreprise.siren}"
    assert response.redirect_chain == [(url, 302)]


@pytest.mark.parametrize("status_est_soumis", [True, False])
@pytest.mark.django_db
def test_premiere_simulation_sur_entreprise_inexistante_en_bdd(
    status_est_soumis, client, mocker
):
    data = {
        "denomination": "Entreprise SAS",
        "siren": "000000001",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "appartient_groupe": True,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
    }

    mocker.patch(
        "reglementations.views.bdese.BDESEReglementation.est_soumis",
        return_value=status_est_soumis,
    )
    mocker.patch(
        "reglementations.views.index_egapro.IndexEgaproReglementation.est_soumis",
        return_value=status_est_soumis,
    )
    mocker.patch(
        "reglementations.views.dispositif_alerte.DispositifAlerteReglementation.est_soumis",
        return_value=status_est_soumis,
    )
    mocker.patch(
        "reglementations.views.bges.BGESReglementation.est_soumis",
        return_value=status_est_soumis,
    )
    mocker.patch(
        "reglementations.views.audit_energetique.AuditEnergetiqueReglementation.est_soumis",
        return_value=status_est_soumis,
    )
    response = client.post("/reglementations", data=data)

    content = response.content.decode("utf-8")
    assert "Entreprise SAS" in content

    # entreprise has been created
    entreprise = Entreprise.objects.get(siren="000000001")
    assert entreprise.denomination == "Entreprise SAS"
    assert entreprise.date_cloture_exercice is None
    assert entreprise.appartient_groupe
    assert entreprise.comptes_consolides
    caracteristiques = entreprise.caracteristiques_actuelles()
    assert caracteristiques.effectif == CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50
    assert caracteristiques.effectif_outre_mer is None
    assert (
        caracteristiques.tranche_chiffre_affaires
        == CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M
    )
    assert (
        caracteristiques.tranche_bilan
        == CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M
    )
    assert (
        caracteristiques.tranche_chiffre_affaires_consolide
        == CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M
    )
    assert (
        caracteristiques.tranche_bilan_consolide
        == CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M
    )
    assert caracteristiques.bdese_accord is None
    assert caracteristiques.systeme_management_energie is None

    # reglementations for this entreprise are anonymously displayed
    context = response.context
    assert context["entreprise"] == entreprise
    assert context["simulation"]
    reglementations = context["reglementations"]
    for index, REGLEMENTATION in enumerate(REGLEMENTATIONS):
        assert reglementations[index]["status"] == REGLEMENTATION(
            entreprise
        ).calculate_status(caracteristiques, AnonymousUser())

    if status_est_soumis:
        assert '<p class="fr-badge">soumis</p>' in content, content
        anonymous_status_detail = "Vous êtes soumis à cette réglementation. Connectez-vous pour en savoir plus."
        assert anonymous_status_detail in content, content
        assert '<p class="fr-badge">non soumis</p>' not in content, content
    else:
        assert '<p class="fr-badge">non soumis</p>' in content, content
        anonymous_status_detail = "Vous n'êtes pas soumis à cette réglementation."
        assert anonymous_status_detail in content, content
        assert '<p class="fr-badge">soumis</p>' not in content, content


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
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "appartient_groupe": True,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
    }

    mocker.patch(
        "reglementations.views.bdese.BDESEReglementation.est_soumis",
        return_value=status_est_soumis,
    )
    mocker.patch(
        "reglementations.views.index_egapro.IndexEgaproReglementation.est_soumis",
        return_value=status_est_soumis,
    )
    mocker.patch(
        "reglementations.views.dispositif_alerte.DispositifAlerteReglementation.est_soumis",
        return_value=status_est_soumis,
    )
    mocker.patch(
        "reglementations.views.bges.BGESReglementation.est_soumis",
        return_value=status_est_soumis,
    )
    mocker.patch(
        "reglementations.views.audit_energetique.AuditEnergetiqueReglementation.est_soumis",
        return_value=status_est_soumis,
    )
    response = client.post("/reglementations", data=data)

    content = response.content.decode("utf-8")
    assert "Une autre entreprise SAS" in content

    reglementations = response.context["reglementations"]
    if status_est_soumis:
        assert '<p class="fr-badge">soumis</p>' in content
        anonymous_status_detail = "L'entreprise est soumise à cette réglementation."
        assert anonymous_status_detail in content, content
    else:
        assert '<p class="fr-badge">non soumis</p>' in content
        anonymous_status_detail = (
            "L'entreprise n'est pas soumise à cette réglementation."
        )
        assert anonymous_status_detail in content, content


def test_lors_d_une_simulation_les_donnees_d_une_entreprise_avec_des_caracteristiques_actuelles_ne_sont_pas_modifiees(
    client, date_cloture_dernier_exercice, entreprise_factory
):
    """
    La simulation sur une entreprise déjà enregistrée en base avec des caracteristiques actuelles ne modifie pas ses caractéristiques
    mais affiche quand même les statuts correspondant aux données utilisées lors de la simulation
    """

    entreprise = entreprise_factory(
        date_cloture_exercice=date_cloture_dernier_exercice - timedelta(days=1),
        appartient_groupe=True,
        comptes_consolides=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_250_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        bdese_accord=True,
        systeme_management_energie=True,
    )
    assert entreprise.caracteristiques_actuelles()

    effectif = CaracteristiquesAnnuelles.EFFECTIF_500_ET_PLUS
    ca = CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M
    bilan = CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M
    autre_denomination = "Autre dénomination"

    data = {
        "denomination": autre_denomination,
        "siren": entreprise.siren,
        "effectif": effectif,
        "tranche_chiffre_affaires": ca,
        "tranche_bilan": bilan,
        "appartient_groupe": False,
        "comptes_consolides": False,
        "tranche_chiffre_affaires_consolide": "",
        "tranche_bilan_consolide": "",
    }

    response = client.post("/reglementations", data=data)

    entreprise.refresh_from_db()
    assert (
        entreprise.date_cloture_exercice
        == date_cloture_dernier_exercice - timedelta(days=1)
    )
    assert entreprise.appartient_groupe
    assert entreprise.comptes_consolides
    caracteristiques = entreprise.caracteristiques_annuelles(
        entreprise.date_cloture_exercice.year
    )
    assert (
        caracteristiques.effectif == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499
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
    assert context["entreprise"] == entreprise
    assert context["entreprise"].denomination == autre_denomination
    assert context["entreprise"].appartient_groupe == False
    assert context["entreprise"].comptes_consolides == False
    reglementations = context["reglementations"]
    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise,
        effectif=effectif,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        tranche_chiffre_affaires=ca,
        tranche_bilan=bilan,
        tranche_chiffre_affaires_consolide=None,
        tranche_bilan_consolide=None,
        bdese_accord=False,
        systeme_management_energie=False,
    )
    for index, REGLEMENTATION in enumerate(REGLEMENTATIONS):
        status = reglementations[index]["status"]
        assert status == REGLEMENTATION(entreprise).calculate_status(
            caracteristiques, AnonymousUser()
        )


def test_lors_d_une_simulation_les_donnees_d_une_entreprise_avec_utilisateur_ne_sont_pas_modifiees(
    client, alice, entreprise_non_qualifiee
):
    """
    La simulation sur une entreprise déjà enregistrée en base avec un utilisateur ne crée pas de caractéristique
    mais affiche quand même les statuts correspondant aux données utilisées lors de la simulation
    """

    entreprise = entreprise_non_qualifiee
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    effectif = CaracteristiquesAnnuelles.EFFECTIF_500_ET_PLUS
    ca = CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M
    bilan = CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M
    autre_denomination = "Autre dénomination"

    data = {
        "denomination": autre_denomination,
        "siren": entreprise.siren,
        "effectif": effectif,
        "tranche_chiffre_affaires": ca,
        "tranche_bilan": bilan,
        "appartient_groupe": True,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": ca,
        "tranche_bilan_consolide": bilan,
    }

    response = client.post("/reglementations", data=data)

    entreprise.refresh_from_db()
    assert entreprise.date_cloture_exercice is None
    assert entreprise.appartient_groupe is None
    assert entreprise.comptes_consolides is None
    assert not entreprise.caracteristiques_actuelles()

    context = response.context
    assert context["entreprise"] == entreprise
    assert context["entreprise"].denomination == autre_denomination
    assert context["entreprise"].appartient_groupe
    assert context["entreprise"].comptes_consolides
    reglementations = context["reglementations"]
    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise,
        effectif=effectif,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        tranche_chiffre_affaires=ca,
        tranche_bilan=bilan,
        tranche_chiffre_affaires_consolide=ca,
        tranche_bilan_consolide=bilan,
        bdese_accord=False,
        systeme_management_energie=False,
    )
    for index, REGLEMENTATION in enumerate(REGLEMENTATIONS):
        status = reglementations[index]["status"]
        assert status == REGLEMENTATION(entreprise).calculate_status(
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

    effectif = CaracteristiquesAnnuelles.EFFECTIF_500_ET_PLUS
    ca = CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M
    bilan = CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M
    autre_denomination = "Autre dénomination"
    data = {
        "denomination": autre_denomination,
        "siren": entreprise.siren,
        "effectif": effectif,
        "tranche_chiffre_affaires": ca,
        "tranche_bilan": bilan,
        "appartient_groupe": True,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": ca,
        "tranche_bilan_consolide": bilan,
    }

    response = client.post("/reglementations", data=data)

    entreprise.refresh_from_db()
    assert entreprise.date_cloture_exercice is None
    assert entreprise.appartient_groupe
    assert entreprise.comptes_consolides
    caracteristiques = entreprise.caracteristiques_actuelles()
    assert caracteristiques.effectif == effectif
    assert caracteristiques.tranche_chiffre_affaires == ca
    assert caracteristiques.tranche_bilan == bilan
    assert caracteristiques.tranche_chiffre_affaires_consolide == ca
    assert caracteristiques.tranche_bilan_consolide == bilan

    context = response.context
    assert context["entreprise"] == entreprise
    assert context["entreprise"].denomination == autre_denomination
    assert context["entreprise"].appartient_groupe
    assert context["entreprise"].comptes_consolides
    reglementations = context["reglementations"]
    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise,
        effectif=effectif,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        tranche_chiffre_affaires=ca,
        tranche_bilan=bilan,
        tranche_chiffre_affaires_consolide=ca,
        tranche_bilan_consolide=bilan,
        bdese_accord=False,
        systeme_management_energie=False,
    )
    for index, REGLEMENTATION in enumerate(REGLEMENTATIONS):
        status = reglementations[index]["status"]
        assert status == REGLEMENTATION(entreprise).calculate_status(
            caracteristiques, AnonymousUser()
        )


def test_should_not_commit_une_entreprise_avec_des_caracteristiques_actuelles_sans_utilisateur(
    client, entreprise_factory
):
    entreprise = entreprise_factory()
    assert entreprise.caracteristiques_actuelles()

    # une simulation ne devrait jamais écraser des caractéristiques existantes
    assert not should_commit(entreprise)


def test_should_not_commit_une_entreprise_avec_des_caracteristiques_actuelles_avec_utilisateur(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory()
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

    response = client.post("/reglementations", data=unvalid_data)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Impossible de finaliser la simulation car le formulaire contient des erreurs."
        in content
    )
    assert Entreprise.objects.count() == 0
    assert CaracteristiquesAnnuelles.objects.count() == 0


def test_reglementations_for_entreprise_with_authenticated_user(client, entreprise):
    client.force_login(entreprise.users.first())

    response = client.get(f"/reglementations/{entreprise.siren}")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    context = response.context
    assert context["entreprise"] == entreprise
    reglementations = context["reglementations"]
    for index, REGLEMENTATION in enumerate(REGLEMENTATIONS):
        assert reglementations[index]["status"] == REGLEMENTATION(
            entreprise
        ).calculate_status(
            entreprise.dernieres_caracteristiques_qualifiantes, entreprise.users.first()
        )
    for reglementation in reglementations:
        assert reglementation["status"].status_detail in content


def test_reglementations_for_entreprise_with_authenticated_user_and_multiple_entreprises(
    client, entreprise_factory, alice
):
    entreprise1 = entreprise_factory(siren="000000001")
    entreprise2 = entreprise_factory(siren="000000002")
    attach_user_to_entreprise(alice, entreprise1, "Présidente")
    attach_user_to_entreprise(alice, entreprise2, "Présidente")
    client.force_login(alice)

    response = client.get(f"/reglementations/{entreprise1.siren}")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    context = response.context
    assert context["entreprise"] == entreprise1
    reglementations = context["reglementations"]
    for index, REGLEMENTATION in enumerate(REGLEMENTATIONS):
        assert reglementations[index]["status"] == REGLEMENTATION(
            entreprise1
        ).calculate_status(entreprise1.dernieres_caracteristiques_qualifiantes, alice)
    for reglementation in reglementations:
        assert reglementation["status"].status_detail in content

    response = client.get(f"/reglementations/{entreprise2.siren}")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    context = response.context
    assert context["entreprise"] == entreprise2
    assert context["simulation"] == False
    reglementations = context["reglementations"]
    for index, REGLEMENTATION in enumerate(REGLEMENTATIONS):
        assert reglementations[index]["status"] == REGLEMENTATION(
            entreprise2
        ).calculate_status(entreprise2.dernieres_caracteristiques_qualifiantes, alice)
    for reglementation in reglementations:
        assert reglementation["status"].status_detail in content


def test_reglementations_for_entreprise_non_qualifiee_redirect_to_qualification_page(
    client, alice, entreprise_non_qualifiee, mock_api_recherche_entreprises
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    client.force_login(alice)

    response = client.get(
        f"/reglementations/{entreprise_non_qualifiee.siren}", follow=True
    )

    assert response.status_code == 200
    url = f"/entreprises/{entreprise_non_qualifiee.siren}"
    assert response.redirect_chain == [(url, 302)]


def test_reglementations_for_entreprise_qualifiee_dans_le_passe(
    client, date_cloture_dernier_exercice, entreprise
):
    with freeze_time(date_cloture_dernier_exercice + timedelta(days=367)):
        client.force_login(entreprise.users.first())
        response = client.get(f"/reglementations/{entreprise.siren}")

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        f"Les informations sont basées sur des données de l'exercice {date_cloture_dernier_exercice.year}."
        in content
    ), content
