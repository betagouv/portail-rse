from datetime import datetime
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import load_workbook

from habilitations.models import attach_user_to_entreprise
from reglementations.models.csrd import DocumentAnalyseIA
from reglementations.models.csrd import RapportCSRD


def test_ajout_document_par_utilisateur_autorise(client, csrd):
    utilisateur = csrd.proprietaire
    client.force_login(utilisateur)
    fichier = SimpleUploadedFile("test.pdf", b"pdf file data")

    response = client.post(
        f"/csrd/{csrd.id}/ajout_document",
        {"fichier": fichier},
        headers={"referer": "http://domain.test/connexion"},
    )

    assert response.status_code == 302
    assert csrd.documents.count() == 1


def test_ajout_document_par_utilisateur_non_autorise(client, csrd, bob):
    assert bob != csrd.proprietaire
    client.force_login(bob)
    fichier = SimpleUploadedFile("test.pdf", b"pdf file data")

    response = client.post(
        f"/csrd/{csrd.id}/ajout_document",
        {"fichier": fichier},
        headers={"referer": "http://domain.test/connexion"},
    )

    assert response.status_code == 403
    assert csrd.documents.count() == 0


def test_ajout_document_sur_csrd_inexistante(client, alice):
    client.force_login(alice)
    fichier = SimpleUploadedFile("test.pdf", b"pdf file data")

    response = client.post(
        f"/csrd/42/ajout_document",
        {"fichier": fichier},
        headers={"referer": "http://domain.test/connexion"},
    )

    assert response.status_code == 404
    assert DocumentAnalyseIA.objects.count() == 0


def test_serveur_ia_poste_l_avancement_de_l_analyse(
    client, alice, entreprise_non_qualifiee
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    csrd = RapportCSRD.objects.create(
        proprietaire=alice,
        entreprise=entreprise_non_qualifiee,
        annee=f"{datetime.now():%Y}",
    )
    document = DocumentAnalyseIA.objects.create(
        rapport_csrd=csrd,
    )
    client.force_login(alice)

    response = client.post(
        f"/ESRS-predict/{document.id}",
        {
            "status": "processing",
        },
    )

    document.refresh_from_db()
    assert document.etat == "processing"

    response = client.post(
        f"/ESRS-predict/{document.id}",
        {
            "status": "error",
            "msg": "MESSAGE",
        },
    )

    document.refresh_from_db()
    assert document.etat == "error"
    assert document.message == "MESSAGE"


def test_serveur_ia_poste_la_reussite_de_l_analyse(
    client, alice, entreprise_non_qualifiee
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    csrd = RapportCSRD.objects.create(
        proprietaire=alice,
        entreprise=entreprise_non_qualifiee,
        annee=f"{datetime.now():%Y}",
    )
    RESULTATS = """{
  "ESRS E1": [
    {
      "PAGES": 1,
      "TEXTS": "A"
    }
  ],
  "ESRS E2": [
    {
      "PAGES": 6,
      "TEXTS": "B"
    },
    {
      "PAGES": 7,
      "TEXTS": "C"
    }
  ]
  }"""
    document = DocumentAnalyseIA.objects.create(
        rapport_csrd=csrd,
    )
    client.force_login(alice)

    response = client.post(
        f"/ESRS-predict/{document.id}",
        {
            "status": "success",
            "resultat_json": RESULTATS,
        },
    )

    document.refresh_from_db()
    assert document.etat == "success"
    assert document.resultat_json == RESULTATS


def test_resultats_ia_d_un_document_au_format_xlsx(
    client, alice, entreprise_non_qualifiee
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    csrd = RapportCSRD.objects.create(
        proprietaire=alice,
        entreprise=entreprise_non_qualifiee,
        annee=f"{datetime.now():%Y}",
    )
    document = DocumentAnalyseIA.objects.create(
        rapport_csrd=csrd,
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
        f"/ESRS-predict/{document.id}/resultats.xlsx",
    )

    assert response["Content-Disposition"] == "filename=resultats.xlsx"
    assert (
        response["content-type"]
        == "application/vnd.openxmlformatsofficedocument.spreadsheetml.sheet"
    )
    workbook = load_workbook(filename=BytesIO(response.content))
    onglet = workbook.active
    assert onglet["A1"].value == "ESRS"
    assert onglet["B1"].value == "PAGE"
    assert onglet["C1"].value == "PHRASE"
    assert onglet["A2"].value == "ESRS E1"
    assert onglet["B2"].value == 1
    assert onglet["C2"].value == "A"
    assert onglet["A3"].value == "ESRS E2"
    assert onglet["B3"].value == 6
    assert onglet["C3"].value == "B"
    assert onglet["A4"].value == "ESRS E2"
    assert onglet["B4"].value == 7
    assert onglet["C4"].value == "C"


def test_resultats_ia_d_un_document_au_format_xlsx_retourne_une_404_si_document_inexistant(
    client, alice
):
    client.force_login(alice)

    response = client.get(
        f"/ESRS-predict/42/resultats.xlsx",
    )

    assert response.status_code == 404


def test_resultats_ia_d_un_document_au_format_xlsx_redirige_vers_la_connexion_si_non_connecté(
    client, alice, entreprise_non_qualifiee
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    csrd = RapportCSRD.objects.create(
        proprietaire=alice,
        entreprise=entreprise_non_qualifiee,
        annee=f"{datetime.now():%Y}",
    )
    document = DocumentAnalyseIA.objects.create(
        rapport_csrd=csrd,
        etat="success",
        resultat_json="""{}""",
    )

    response = client.get(
        f"/ESRS-predict/{document.id}/resultats.xlsx",
    )

    assert response.status_code == 302


def test_resultats_ia_de_l_ensemble_des_documents_au_format_xlsx(
    client, alice, entreprise_non_qualifiee
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    csrd = RapportCSRD.objects.create(
        proprietaire=alice,
        entreprise=entreprise_non_qualifiee,
        annee=f"{datetime.now():%Y}",
    )
    DocumentAnalyseIA.objects.create(
        rapport_csrd=csrd,
        etat="success",
        resultat_json="""{
  "ESRS E1": [
    {
      "PAGES": 1,
      "TEXTS": "A"
    }
  ]
  }""",
    )
    DocumentAnalyseIA.objects.create(
        rapport_csrd=csrd,
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
        f"/ESRS-predict/{csrd.id}/synthese_resultats.xlsx",
    )

    assert response["Content-Disposition"] == "filename=synthese_resultats.xlsx"
    assert (
        response["content-type"]
        == "application/vnd.openxmlformatsofficedocument.spreadsheetml.sheet"
    )
    workbook = load_workbook(filename=BytesIO(response.content))
    onglet = workbook.active
    assert onglet["A1"].value == "ESRS"
    assert onglet["B1"].value == "FICHIER"
    assert onglet["C1"].value == "PAGE"
    assert onglet["D1"].value == "PHRASE"
    assert onglet["A2"].value == "ESRS E1"
    assert onglet["C2"].value == 1
    assert onglet["D2"].value == "A"
    assert onglet["A3"].value == "ESRS E2"
    assert onglet["C3"].value == 6
    assert onglet["D3"].value == "B"


def test_resultats_ia_de_l_ensemble_des_documents_retourne_une_404_si_csrd_inexistant(
    client, alice
):
    client.force_login(alice)

    response = client.get(
        "/ESRS-predict/42/synthese_resultats.xlsx",
    )

    assert response.status_code == 404


def test_resultats_ia_de_l_ensemble_des_documents_redirige_vers_la_connexion_si_non_connecté(
    client, alice, entreprise_non_qualifiee
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    csrd = RapportCSRD.objects.create(
        proprietaire=alice,
        entreprise=entreprise_non_qualifiee,
        annee=f"{datetime.now():%Y}",
    )

    response = client.get(
        f"/ESRS-predict/{csrd.id}/synthese_resultats.xlsx",
    )

    assert response.status_code == 302
