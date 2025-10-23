from io import BytesIO

from django.urls import reverse
from openpyxl import load_workbook

from analyseia.models import AnalyseIA


def test_telechargement_des_resultats_IA_d_un_document_au_format_xlsx(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    document = AnalyseIA.objects.create(
        etat="success",
        resultat_json="""{
  "ESRS E1": [
    {
      "PAGES": 1,
      "TEXTS": "A"
    }
  ],
  "ESRS E2 : Pollution": [
    {
      "PAGES": 6,
      "TEXTS": "B"
    },
    {
      "PAGES": 7,
      "TEXTS": "C"
    }
  ]
  }""",
    )

    client.force_login(alice)

    response = client.get(
        reverse("analyseia:resultat", args=[entreprise.siren, document.id]),
    )

    assert response["Content-Disposition"] == "filename=resultats.xlsx"
    assert (
        response["content-type"]
        == "application/vnd.openxmlformatsofficedocument.spreadsheetml.sheet"
    )
    workbook = load_workbook(filename=BytesIO(response.content))
    onglet = workbook[">>>"]
    assert not onglet["C14"].value
    onglet = workbook["Phrases relatives aux ESG"]
    assert onglet["A1"].value == "Thème"
    assert onglet["B1"].value == "Fichier"
    assert onglet["C1"].value == "Page"
    assert onglet["D1"].value == "Phrase"
    assert onglet["A2"].value == "Changement climatique"
    assert onglet["C2"].value == 1
    assert onglet["D2"].value == "A"
    assert onglet["A3"].value == "Pollution"
    assert onglet["C3"].value == 6
    assert onglet["D3"].value == "B"
    assert onglet["A4"].value == "Pollution"
    assert onglet["C4"].value == 7
    assert onglet["D4"].value == "C"


def test_telechargement_des_resultats_IA_d_un_document_inexistant(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    response = client.get(
        reverse("analyseia:resultat", args=[entreprise.siren, 42]),
    )

    assert response.status_code == 404


def test_telechargement_des_resultats_IA_d_un_document_redirige_vers_la_connexion_si_non_connecté(
    client, entreprise_factory, alice, analyse
):
    entreprise = entreprise_factory(siren="000000089", utilisateur=alice)

    response = client.get(
        reverse("analyseia:resultat", args=[entreprise.siren, analyse.id]),
    )

    assert response.status_code == 302


def test_telechargement_des_resultats_ia_de_l_ensemble_des_documents_au_format_xlsx(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    document = entreprise.analyses_ia.create(
        etat="success",
        resultat_json="""{
  "ESRS E1": [
    {
      "PAGES": 1,
      "TEXTS": "A"
    }
   ],
    "Non ESRS": [
    {
      "PAGES": 22,
      "TEXTS": "X"
    }
  ]
  }""",
    )

    document = entreprise.analyses_ia.create(
        etat="success",
        resultat_json="""{
  "ESRS E2": [
    {
      "PAGES": 6,
      "TEXTS": "B"
    }
  ]
  }""",
    )

    client.force_login(alice)

    response = client.get(
        reverse("analyseia:synthese_resultat", args=[entreprise.siren]),
    )

    assert response["Content-Disposition"] == "filename=synthese_resultats.xlsx"
    assert (
        response["content-type"]
        == "application/vnd.openxmlformatsofficedocument.spreadsheetml.sheet"
    )
    workbook = load_workbook(filename=BytesIO(response.content))
    onglet = workbook[">>>"]
    assert onglet["C14"].value == "Synthèse générique"
    onglet = workbook["Phrases relatives aux ESG"]
    assert onglet["A1"].value == "Thème"
    assert onglet["B1"].value == "Fichier"
    assert onglet["C1"].value == "Page"
    assert onglet["D1"].value == "Phrase"
    assert onglet["A2"].value == "Changement climatique"
    assert onglet["C2"].value == 1
    assert onglet["D2"].value == "A"
    assert onglet["A3"].value == "Pollution"
    assert onglet["C3"].value == 6
    assert onglet["D3"].value == "B"


def test_telechargement_des_resultats_IA_de_l_ensemble_des_documents_redirige_vers_la_connexion_si_non_connecté(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)

    response = client.get(
        reverse("analyseia:synthese_resultat", args=[entreprise.siren]),
    )

    assert response.status_code == 302


def test_telechargement_des_resultats_par_ESRS_au_format_xlsx(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    document = entreprise.analyses_ia.create(
        etat="success",
        resultat_json="""{
  "ESRS E1": [
    {
      "PAGES": 1,
      "TEXTS": "A"
    }
  ],
  "ESRS E2": [
    {
      "PAGES": 4,
      "TEXTS": "B"
    }
  ],
  "Non ESRS": [
    {
      "PAGES": 22,
      "TEXTS": "X"
    }
  ]
  }""",
    )
    document = entreprise.analyses_ia.create(
        etat="success",
        resultat_json="""{
  "ESRS E2": [
    {
      "PAGES": 6,
      "TEXTS": "C"
    }
  ]
  }""",
    )

    client.force_login(alice)

    response = client.get(
        reverse("analyseia:synthese_resultat_par_ESRS", args=[entreprise.siren, "E2"]),
    )

    assert response["Content-Disposition"] == "filename=resultats_ESRS_E2.xlsx"
    assert (
        response["content-type"]
        == "application/vnd.openxmlformatsofficedocument.spreadsheetml.sheet"
    )
    workbook = load_workbook(filename=BytesIO(response.content))
    onglet = workbook[">>>"]
    assert onglet["C14"].value == "Pollution"
    onglet = workbook["Phrases relatives aux ESG"]
    assert onglet["A1"].value == "Thèmes"
    assert onglet["B1"].value == "Fichier"
    assert onglet["C1"].value == "Page"
    assert onglet["D1"].value == "Phrase"
    assert onglet["A2"].value == "Pollution"
    assert onglet["C2"].value == 4
    assert onglet["D2"].value == "B"
    assert onglet["A3"].value == "Pollution"
    assert onglet["C3"].value == 6
    assert onglet["D3"].value == "C"


def test_telechargement_des_resultats_IA_par_ESRS_d_une_entreprise_inexistante(
    client, alice
):
    client.force_login(alice)

    response = client.get(
        reverse("analyseia:synthese_resultat_par_ESRS", args=["123456789", "E2"]),
    )

    assert response.status_code == 404


def test_telechargement_des_resultats_IA_par_ESRS_redirige_vers_la_connexion_si_non_connecté(
    client,
    entreprise_factory,
    alice,
):
    entreprise = entreprise_factory(utilisateur=alice)

    response = client.get(
        reverse("analyseia:synthese_resultat_par_ESRS", args=[entreprise.siren, "E2"]),
    )

    assert response.status_code == 302
