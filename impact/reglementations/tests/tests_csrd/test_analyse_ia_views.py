from django.core.files.uploadedfile import SimpleUploadedFile

from reglementations.models.csrd import DocumentAnalyseIA


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
