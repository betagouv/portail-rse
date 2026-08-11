from datetime import date

from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import Habilitation


def test_page_anticipation_avec_entreprise_qualifiee_initialise_les_champs_sans_appel_api(
    client,
    alice,
    entreprise_factory,
    mock_api_infos_entreprise,
):
    entreprise = entreprise_factory(
        date_cloture_exercice=date(2026, 12, 31),
        appartient_groupe=True,
        est_societe_mere=True,
        societe_mere_en_france=True,
        comptes_consolides=True,
        est_cotee=True,
        est_interet_public=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        effectif_securite_sociale=CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_ENTRE_50_ET_249,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        effectif_groupe_france=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        bdese_accord=True,
        tranche_consommation_energie_finale=CaracteristiquesAnnuelles.CONSOMMATION_ENERGIE_MOINS_DE_2_75GWH,
    )
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    client.force_login(alice)

    response = client.get(
        reverse("reglementations:anticipation", kwargs={"siren": entreprise.siren})
    )

    assert response.status_code == 200
    assertTemplateUsed(response, "reglementations/tableau_de_bord/anticipation.html")
    mock_api_infos_entreprise.assert_not_called()
    context = response.context

    form = context["form"]

    # sqlite automatically converts dates to strings,
    # postgres doesn't (datetime).
    assert form["effectif"].initial == CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10
    assert (
        form["effectif_securite_sociale"].initial
        == CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_ENTRE_50_ET_249
    )
    assert (
        form["tranche_chiffre_affaires"].initial
        == CaracteristiquesAnnuelles.CA_MOINS_DE_900K
    )
    assert (
        form["tranche_bilan"].initial == CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K
    )
    assert form["est_cotee"].initial
    assert form["est_interet_public"].initial
    assert form["appartient_groupe"].initial
    assert (
        form["effectif_groupe"].initial
        == CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    )
    assert (
        form["effectif_groupe_france"].initial
        == CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    )
    assert form["est_societe_mere"].initial
    assert form["societe_mere_en_france"].initial
    assert form["comptes_consolides"].initial
    assert (
        form["tranche_chiffre_affaires_consolide"].initial
        == CaracteristiquesAnnuelles.CA_100M_ET_PLUS
    )
    assert (
        form["tranche_bilan_consolide"].initial
        == CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS
    )
    assert form["bdese_accord"].initial
    assert (
        form["tranche_consommation_energie_finale"].initial
        == CaracteristiquesAnnuelles.CONSOMMATION_ENERGIE_MOINS_DE_2_75GWH
    )


def test_lors_d_une_anticipation_les_donnees_d_une_entreprise_avec_utilisateur_ne_sont_pas_modifiees(
    client, alice, entreprise_factory, mocker
):
    """
    Une anticipation ne modifie pas de caractéristique
    mais calcule quand même les résultats correspondant aux données utilisées lors de la simulation
    """

    donnees_initiales = {
        "date_cloture_exercice": date(2026, 12, 31),
        "appartient_groupe": True,
        "est_societe_mere": True,
        "societe_mere_en_france": True,
        "comptes_consolides": True,
        "est_cotee": True,
        "est_interet_public": True,
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "effectif_securite_sociale": CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        "effectif_groupe_france": CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        "bdese_accord": True,
        "tranche_consommation_energie_finale": CaracteristiquesAnnuelles.CONSOMMATION_ENERGIE_MOINS_DE_2_75GWH,
    }
    entreprise = entreprise_factory(**donnees_initiales)

    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    client.force_login(alice)

    effectif = CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    effectif_groupe = CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    effectif_securite_sociale = (
        CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_500_ET_PLUS
    )
    effectif_outre_mer = CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_250_ET_PLUS
    ca = CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M
    bilan = CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M
    ca_consolide = CaracteristiquesAnnuelles.CA_100M_ET_PLUS
    bilan_consolide = CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS
    autre_denomination = "Autre dénomination"
    autre_categorie_juridique_sirene = 5200
    data = {
        "siren": entreprise.siren,
        "denomination": autre_denomination,
        "categorie_juridique_sirene": autre_categorie_juridique_sirene,
        "date_cloture_exercice": date(2026, 8, 13),
        "effectif": effectif,
        "effectif_securite_sociale": effectif_securite_sociale,
        "effectif_outre_mer": effectif_outre_mer,
        "tranche_chiffre_affaires": ca,
        "tranche_bilan": bilan,
        "est_cotee": True,
        "appartient_groupe": True,
        "est_societe_mere": True,
        "effectif_groupe": effectif_groupe,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": ca_consolide,
        "tranche_bilan_consolide": bilan_consolide,
        "tranche_consommation_energie_finale": donnees_initiales[
            "tranche_consommation_energie_finale"
        ],
    }

    mock_est_soumis = mocker.patch(
        "reglementations.views.base.Reglementation.est_soumis"
    )

    response = client.post(
        reverse("reglementations:anticipation", kwargs={"siren": entreprise.siren}),
        data=data,
        follow=True,
    )

    entreprise.refresh_from_db()
    assert entreprise.date_cloture_exercice == date(2026, 12, 31)
    assert entreprise.categorie_juridique_sirene != autre_categorie_juridique_sirene
    assert not entreprise.caracteristiques_actuelles()

    assert mock_est_soumis.called
    caracteristiques_simulees = mock_est_soumis.call_args.args[0]
    assert caracteristiques_simulees.entreprise.siren == entreprise.siren
    assert caracteristiques_simulees.entreprise.denomination == entreprise.denomination
    assert (
        caracteristiques_simulees.entreprise.categorie_juridique_sirene
        == entreprise.categorie_juridique_sirene
    )
    assert (
        caracteristiques_simulees.entreprise.code_pays_etranger_sirene
        == entreprise.code_pays_etranger_sirene
    )
    assert caracteristiques_simulees.effectif == effectif
    assert caracteristiques_simulees.effectif_outre_mer == effectif_outre_mer
    assert caracteristiques_simulees.tranche_chiffre_affaires == ca
    assert caracteristiques_simulees.tranche_bilan == bilan
    assert caracteristiques_simulees.entreprise.est_cotee == data["est_cotee"]
    assert (
        caracteristiques_simulees.entreprise.appartient_groupe
        == data["appartient_groupe"]
    )
    assert (
        caracteristiques_simulees.entreprise.est_societe_mere
        == data["est_societe_mere"]
    )
    assert caracteristiques_simulees.effectif_groupe == effectif_groupe
    assert (
        caracteristiques_simulees.entreprise.comptes_consolides
        == data["comptes_consolides"]
    )
    assert caracteristiques_simulees.tranche_chiffre_affaires_consolide == ca_consolide
    assert caracteristiques_simulees.tranche_bilan_consolide == bilan_consolide

    assertTemplateUsed(response, "reglementations/tableau_de_bord/reglementations.html")


def test_anticipation_avec_un_formulaire_invalide_affiche_un_message_d_erreur(
    client, alice, entreprise_factory
):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    client.force_login(alice)

    response = client.post(
        reverse("reglementations:anticipation", kwargs={"siren": entreprise.siren}),
        data={"date_cloture_exercice": "date-invalide"},
        follow=True,
    )

    assert response.status_code == 200
    assertTemplateUsed(response, "reglementations/tableau_de_bord/anticipation.html")
    messages = list(response.context["messages"])
    assert (
        messages[0].message
        == "Impossible de finaliser cet essai car le formulaire contient des erreurs."
    )
