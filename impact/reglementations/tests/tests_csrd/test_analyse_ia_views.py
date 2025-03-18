from io import BytesIO

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from openpyxl import load_workbook

from reglementations.models.csrd import DocumentAnalyseIA
from utils.mock_response import MockedResponse


CONTENU_PDF = b"%PDF-1.4\n%\xd3\xeb\xe9\xe1\n1 0 obj\n<</Title (CharteEngagements"


def test_ajout_document_par_utilisateur_autorise(client, csrd):
    utilisateur = csrd.proprietaire
    client.force_login(utilisateur)
    fichier = SimpleUploadedFile("test.pdf", CONTENU_PDF)

    response = client.post(
        f"/csrd/{csrd.id}/ajout_document",
        {"fichier": fichier},
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "reglementations:gestion_csrd",
        kwargs={
            "siren": csrd.entreprise.siren,
            "id_etape": "analyse-ecart",
        },
    )
    assert csrd.documents.count() == 1


def test_ajout_document_par_utilisateur_non_autorise(client, csrd, bob):
    assert bob != csrd.proprietaire
    client.force_login(bob)
    fichier = SimpleUploadedFile("test.pdf", CONTENU_PDF)

    response = client.post(
        f"/csrd/{csrd.id}/ajout_document",
        {"fichier": fichier},
    )

    assert response.status_code == 403
    assert csrd.documents.count() == 0


def test_ajout_document_sur_csrd_inexistante(client, alice):
    client.force_login(alice)
    fichier = SimpleUploadedFile("test.pdf", CONTENU_PDF)

    response = client.post(
        f"/csrd/42/ajout_document",
        {"fichier": fichier},
    )

    assert response.status_code == 404
    assert DocumentAnalyseIA.objects.count() == 0


def test_ajout_document_sans_extension_pdf(client, csrd):
    utilisateur = csrd.proprietaire
    client.force_login(utilisateur)
    fichier = SimpleUploadedFile("test.odt", b"libre office writer data")

    response = client.post(
        f"/csrd/{csrd.id}/ajout_document",
        {"fichier": fichier},
    )

    assert response.status_code == 400
    assert csrd.documents.count() == 0


def test_ajout_document_dont_le_contenu_n_est_pas_du_pdf(client, csrd):
    utilisateur = csrd.proprietaire
    client.force_login(utilisateur)
    fichier = SimpleUploadedFile("test.pdf", b"pas un pdf")

    response = client.post(
        f"/csrd/{csrd.id}/ajout_document",
        {"fichier": fichier},
    )

    assert response.status_code == 400
    assert csrd.documents.count() == 0


def test_suppression_document_par_utilisateur_autorise(client, document):
    utilisateur = document.rapport_csrd.proprietaire
    client.force_login(utilisateur)

    response = client.post(f"/csrd/{document.id}/suppression")

    assert response.status_code == 302
    assert response.url == reverse(
        "reglementations:gestion_csrd",
        kwargs={
            "siren": document.rapport_csrd.entreprise.siren,
            "id_etape": "analyse-ecart",
        },
    )
    assert DocumentAnalyseIA.objects.count() == 0


def test_suppression_document_par_utilisateur_non_autorise(client, document, bob):
    assert bob != document.rapport_csrd.proprietaire
    client.force_login(bob)

    response = client.post(f"/csrd/{document.id}/suppression")

    assert response.status_code == 403
    assert DocumentAnalyseIA.objects.count() == 1


def test_suppression_document_inexistant(client, document, alice):
    client.force_login(alice)

    response = client.post(f"/csrd/42/suppression")

    assert response.status_code == 404
    assert DocumentAnalyseIA.objects.count() == 1


def test_lancement_d_analyse_IA(client, mocker, document):
    utilisateur = document.rapport_csrd.proprietaire
    client.force_login(utilisateur)
    ia_request = mocker.patch(
        "requests.post", return_value=MockedResponse(200, {"status": "processing"})
    )

    response = client.post(
        f"/ESRS-predict/{document.id}/start",
    )

    ia_request.assert_called_once_with(
        f"{settings.IA_BASE_URL}/run-task",
        {"document_id": document.id, "url": document.fichier.url},
    )
    document.refresh_from_db()
    assert document.etat == "processing"


def test_lancement_d_anlyse_IA_redirige_vers_la_connexion_si_non_connecté(
    client, mocker, document
):
    response = client.post(
        f"/ESRS-predict/{document.id}/start",
    )

    assert response.status_code == 302
    assert not document.etat


def test_serveur_IA_envoie_l_etat_d_avancement_de_l_analyse(client, document):
    utilisateur = document.rapport_csrd.proprietaire
    client.force_login(utilisateur)

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


def test_serveur_IA_envoie_le_resultat_de_l_analyse(client, document):
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
    utilisateur = document.rapport_csrd.proprietaire
    client.force_login(utilisateur)

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


def test_telechargement_des_resultats_IA_d_un_document_au_format_xlsx(client, csrd):
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
  ],
  "Non ESRS": [
    {
      "PAGES": 4,
      "TEXTS": "D"
    }
  ]
  }""",
    )
    client.force_login(csrd.proprietaire)

    response = client.get(
        f"/ESRS-predict/{document.id}/resultats.xlsx",
    )

    assert response["Content-Disposition"] == "filename=resultats.xlsx"
    assert (
        response["content-type"]
        == "application/vnd.openxmlformatsofficedocument.spreadsheetml.sheet"
    )
    workbook = load_workbook(filename=BytesIO(response.content))
    onglet = workbook["Phrases trouvées"]
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
    onglet = workbook["Non trouvées"]
    assert onglet["A1"].value == "ESRS"
    assert onglet["B1"].value == "PAGE"
    assert onglet["C1"].value == "PHRASE"
    assert onglet["A2"].value == "Non ESRS"
    assert onglet["B2"].value == 4
    assert onglet["C2"].value == "D"


def test_telechargement_des_resultats_IA_d_un_document_inexistant(client, alice):
    client.force_login(alice)

    response = client.get(
        f"/ESRS-predict/42/resultats.xlsx",
    )

    assert response.status_code == 404


def test_telechargement_des_resultats_IA_d_un_document_redirige_vers_la_connexion_si_non_connecté(
    client, document
):
    response = client.get(
        f"/ESRS-predict/{document.id}/resultats.xlsx",
    )

    assert response.status_code == 302


def test_telechargement_des_resultats_ia_de_l_ensemble_des_documents_au_format_xlsx(
    client, csrd
):
    DocumentAnalyseIA.objects.create(
        rapport_csrd=csrd,
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
      "PAGES": 4,
      "TEXTS": "C"
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
  ],
  "Non ESRS": [
    {
      "PAGES": 8,
      "TEXTS": "D"
    }
  ]
  }""",
    )

    client.force_login(csrd.proprietaire)

    response = client.get(
        f"/ESRS-predict/{csrd.id}/synthese_resultats.xlsx",
    )

    assert response["Content-Disposition"] == "filename=synthese_resultats.xlsx"
    assert (
        response["content-type"]
        == "application/vnd.openxmlformatsofficedocument.spreadsheetml.sheet"
    )
    workbook = load_workbook(filename=BytesIO(response.content))
    onglet = workbook["Phrases trouvées"]
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
    onglet = workbook["Non trouvées"]
    assert onglet["A1"].value == "ESRS"
    assert onglet["B1"].value == "FICHIER"
    assert onglet["C1"].value == "PAGE"
    assert onglet["D1"].value == "PHRASE"
    assert onglet["A2"].value == "Non ESRS"
    assert onglet["C2"].value == 4
    assert onglet["D2"].value == "C"
    assert onglet["A3"].value == "Non ESRS"
    assert onglet["C3"].value == 8
    assert onglet["D3"].value == "D"


def test_telechargement_des_resultats_IA_de_l_ensemble_des_documents_d_un_rapport_csrd_inexistant(
    client, alice
):
    client.force_login(alice)

    response = client.get(
        "/ESRS-predict/42/synthese_resultats.xlsx",
    )

    assert response.status_code == 404


def test_telechargement_des_resultats_IA_de_l_ensemble_des_documents_redirige_vers_la_connexion_si_non_connecté(
    client, csrd
):
    response = client.get(
        f"/ESRS-predict/{csrd.id}/synthese_resultats.xlsx",
    )

    assert response.status_code == 302
