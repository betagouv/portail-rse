from io import BytesIO

from django.urls import reverse
from openpyxl import load_workbook


def test_telechargement_des_resultats_IA_d_un_document_au_format_xlsx(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    document = entreprise.analyses_ia.create(
        nom="NOM.pdf",
        etat_v2="success",
        resultat_json_v2={
            "B3-30-p1": [
                {
                    "unite": "tonne",
                    "valeur": "12",
                    "paragraphe": "Emission de 12 tonnes environ",
                    "champ_id": "estimation_emissions_GES",
                    "colonne_id": "scope_1",
                },
                {
                    "unite": None,
                    "valeur": "1234",
                    "paragraphe": "PARAGRAPHE",
                    "champ_id": "estimation_emissions_GES",
                    "colonne_id": None,
                },
            ]
        },
    )

    client.force_login(alice)

    response = client.get(
        reverse("analyseia:resultat_v2", args=[document.id]),
    )

    assert response["Content-Disposition"] == "filename=resultats_vsme.xlsx"
    assert (
        response["content-type"]
        == "application/vnd.openxmlformatsofficedocument.spreadsheetml.sheet"
    )
    workbook = load_workbook(filename=BytesIO(response.content))
    onglet = workbook["Informations VSME"]
    assert onglet["A1"].value == "Indicateur"
    assert onglet["B1"].value == "Fichier"
    assert onglet["C1"].value == "Champ"
    assert onglet["D1"].value == "Colonne"
    assert onglet["E1"].value == "Valeur"
    assert onglet["F1"].value == "Unité"
    assert onglet["G1"].value == "Paragraphe"
    assert (
        onglet["A2"].value == "Estimation des émissions brutes de GES des scopes 1 et 2"
    )  # "B3-30-p1" / "titre"
    assert onglet["B2"].value == "NOM.pdf"
    assert (
        onglet["C2"].value
        == "Estimation des émissions brutes de gaz à effet de serre des scopes 1 et 2"
    )  # "B3-30-p1" / premier champ
    assert (
        onglet["D2"].value == "Scope 1"
    )  # "B3-30-p1" / premier champ / colonne scope_1 / "label"
    assert onglet["E2"].value == "12"
    assert onglet["F2"].value == "tonne"
    assert onglet["G2"].value == "Emission de 12 tonnes environ"
    assert (
        onglet["A3"].value == "Estimation des émissions brutes de GES des scopes 1 et 2"
    )  # "B3-30-p1" / "titre"
    assert onglet["B3"].value == "NOM.pdf"
    assert (
        onglet["C3"].value
        == "Estimation des émissions brutes de gaz à effet de serre des scopes 1 et 2"
    )
    assert not onglet["D3"].value
    assert onglet["E3"].value == "1234"
    assert not onglet["F3"].value
    assert onglet["G3"].value == "PARAGRAPHE"


def test_telechargement_des_resultats_IA_d_une_analyse_non_terminee(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    analyse = entreprise.analyses_ia.create(
        etat_v2="processing",
    )

    client.force_login(alice)

    response = client.get(
        reverse("analyseia:resultat_v2", args=[analyse.id]),
    )

    assert response["Content-Disposition"] == "filename=resultats_vsme.xlsx"
    assert (
        response["content-type"]
        == "application/vnd.openxmlformatsofficedocument.spreadsheetml.sheet"
    )
    workbook = load_workbook(filename=BytesIO(response.content))


def test_telechargement_des_resultats_IA_d_un_document_inexistant(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    response = client.get(
        reverse("analyseia:resultat_v2", args=[42]),
    )

    assert response.status_code == 404


def test_telechargement_des_resultats_IA_d_un_document_redirige_vers_la_connexion_si_non_connecté(
    client, entreprise_factory, alice, analyse
):
    entreprise = entreprise_factory(siren="000000089", utilisateur=alice)

    response = client.get(
        reverse("analyseia:resultat_v2", args=[analyse.id]),
    )

    assert response.status_code == 302
